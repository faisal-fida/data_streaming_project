import json
import logging
import psycopg2
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import time
import os
import uuid
from jsonschema import validate, ValidationError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(correlation_id)s] %(message)s",
)
logger = logging.getLogger("consumer")

# JSON schema for sensor data validation
sensor_schema = {
    "type": "object",
    "properties": {
        "sensor_id": {"type": "integer"},
        "temperature": {"type": "number"},
        "humidity": {"type": "number"},
        "timestamp": {"type": "integer"},
    },
    "required": ["sensor_id", "temperature", "humidity", "timestamp"],
}


def connect_db():
    conn = None
    while conn is None:
        try:
            conn = psycopg2.connect(
                host=os.getenv("POSTGRES_HOST", "localhost"),
                database=os.getenv("POSTGRES_DB", "sensor_db"),
                user=os.getenv("POSTGRES_USER", "postgres"),
                password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            )
            logger.info(
                "Connected to PostgreSQL and ensured table exists.",
                extra={"correlation_id": "N/A"},
            )
        except Exception as e:
            logger.error(
                f"Database connection failed: {e}", extra={"correlation_id": "N/A"}
            )
            time.sleep(5)
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
        os.getenv("KAFKA_TOPIC", "sensor_data"),
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id=os.getenv("KAFKA_CONSUMER_GROUP", "sensor-group"),
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )

    conn = connect_db()
    create_table(conn)

    logger.info(
        "Starting Kafka consumer, listening to topic...",
        extra={"correlation_id": "N/A"},
    )
    try:
        for message in consumer:
            correlation_id = str(uuid.uuid4())
            data = message.value
            try:
                validate(instance=data, schema=sensor_schema)
                logger.info(
                    f"Received data: {data}", extra={"correlation_id": correlation_id}
                )
                insert_data(conn, data)
            except ValidationError as ve:
                logger.error(
                    f"Schema validation error: {ve.message}",
                    extra={"correlation_id": correlation_id},
                )
            except Exception as e:
                logger.error(
                    f"Failed to insert data: {e}",
                    extra={"correlation_id": correlation_id},
                )
    except KeyboardInterrupt:
        logger.info("Consumer stopped.", extra={"correlation_id": "N/A"})
    except KafkaError as e:
        logger.error(f"Kafka error: {e}", extra={"correlation_id": "N/A"})
    finally:
        if conn:
            conn.close()
        consumer.close()


if __name__ == "__main__":
    main()
