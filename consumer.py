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
    max_retries = 5
    retry_count = 0

    while True:
        try:
            consumer = KafkaConsumer(
                os.getenv("KAFKA_TOPIC", "sensor_data"),
                bootstrap_servers=os.getenv(
                    "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
                ),
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                group_id=os.getenv("KAFKA_CONSUMER_GROUP", "sensor-group"),
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                # Add consumer timeout for better error handling
                consumer_timeout_ms=30000,
                # Add security settings
                security_protocol=os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
            )

            # Reset retry count on successful connection
            retry_count = 0

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
                            f"Received data: {data}",
                            extra={"correlation_id": correlation_id},
                        )
                        insert_data(conn, data)
                    except ValidationError as ve:
                        logger.error(
                            f"Schema validation error: {ve.message}",
                            extra={"correlation_id": correlation_id},
                        )
                    except psycopg2.Error as pe:
                        logger.error(
                            f"Database error: {pe}",
                            extra={"correlation_id": correlation_id},
                        )
                        # Reconnect to database if connection is lost
                        conn = connect_db()
                    except Exception as e:
                        logger.error(
                            f"Failed to process data: {e}",
                            extra={"correlation_id": correlation_id},
                        )
            except KeyboardInterrupt:
                logger.info("Consumer stopped.", extra={"correlation_id": "N/A"})
                break
            except KafkaError as e:
                logger.error(f"Kafka error: {e}", extra={"correlation_id": "N/A"})
                # Sleep before reconnecting
                time.sleep(5)
            finally:
                if conn:
                    conn.close()
                consumer.close()

        except KafkaError as ke:
            retry_count += 1
            wait_time = min(30, 2**retry_count)  # Exponential backoff
            logger.error(
                f"Failed to connect to Kafka (attempt {retry_count}/{max_retries}): {ke}. "
                f"Retrying in {wait_time} seconds...",
                extra={"correlation_id": "N/A"},
            )

            if retry_count >= max_retries:
                logger.critical(
                    "Maximum retry attempts reached. Exiting...",
                    extra={"correlation_id": "N/A"},
                )
                break

            time.sleep(wait_time)
        except KeyboardInterrupt:
            logger.info("Consumer stopped by user.", extra={"correlation_id": "N/A"})
            break


if __name__ == "__main__":
    main()
