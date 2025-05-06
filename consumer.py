import json
import logging
import psycopg2
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("consumer")


def connect_db():
    conn = psycopg2.connect(
        host="localhost", database="sensor_db", user="postgres", password="postgres"
    )
    return conn


def create_table(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sensor_data (
                sensor_id INT,
                temperature FLOAT,
                humidity FLOAT,
                timestamp BIGINT
            )
        """)
        conn.commit()


def insert_data(conn, data):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO sensor_data (sensor_id, temperature, humidity, timestamp)
            VALUES (%s, %s, %s, %s)
        """,
            (
                data["sensor_id"],
                data["temperature"],
                data["humidity"],
                data["timestamp"],
            ),
        )
        conn.commit()


def main():
    consumer = KafkaConsumer(
        "sensor_data",
        bootstrap_servers="localhost:9092",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="sensor-group",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )

    conn = None
    while conn is None:
        try:
            conn = connect_db()
            create_table(conn)
            logger.info("Connected to PostgreSQL and ensured table exists.")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            time.sleep(5)

    logger.info("Starting Kafka consumer, listening to topic 'sensor_data'...")
    try:
        for message in consumer:
            data = message.value
            logger.info(f"Received data: {data}")
            try:
                insert_data(conn, data)
            except Exception as e:
                logger.error(f"Failed to insert data: {e}")
    except KeyboardInterrupt:
        logger.info("Consumer stopped.")
    except KafkaError as e:
        logger.error(f"Kafka error: {e}")
    finally:
        if conn:
            conn.close()
        consumer.close()


if __name__ == "__main__":
    main()
