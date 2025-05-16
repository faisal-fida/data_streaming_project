import time
import random
from confluent_kafka import Producer
from fastavro import parse_schema, schemaless_writer
import io
import logging
import os
import uuid


# Set up a filter to add correlation_id to log records
class CorrelationIDFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, "correlation_id"):
            record.correlation_id = "N/A"
        return True


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(correlation_id)s] %(message)s",
)
logger = logging.getLogger("producer")
logger.addFilter(CorrelationIDFilter())

# Avro schema for sensor data
schema = {
    "type": "record",
    "name": "SensorData",
    "fields": [
        {"name": "sensor_id", "type": "int"},
        {"name": "temperature", "type": "float"},
        {"name": "humidity", "type": "float"},
        {"name": "timestamp", "type": "long"},
    ],
}
parsed_schema = parse_schema(schema)


def get_sample_data():
    """Generate sample data to stream."""
    data = {
        "sensor_id": random.randint(1, 10),
        "temperature": round(random.uniform(20.0, 30.0), 2),
        "humidity": round(random.uniform(30.0, 50.0), 2),
        "timestamp": int(time.time()),
    }
    return data


def delivery_report(err, msg, correlation_id):
    if err is not None:
        logger.error(
            f"Message delivery failed: {err}", extra={"correlation_id": correlation_id}
        )
    else:
        logger.info(
            f"Message delivered to {msg.topic()} [{msg.partition()}]",
            extra={"correlation_id": correlation_id},
        )


def serialize_avro(data, schema):
    bytes_writer = io.BytesIO()
    schemaless_writer(bytes_writer, schema, data)
    return bytes_writer.getvalue()


def main():
    max_retries = 5
    retry_count = 0

    while True:
        try:
            conf = {
                "bootstrap.servers": os.getenv(
                    "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
                ),
                # Add error handling configuration
                "error_cb": lambda err: logger.error(
                    f"Kafka error: {err}", extra={"correlation_id": "N/A"}
                ),
                # Add logging configuration
                "logger": logger,
                # Add security settings (if needed)
                "security.protocol": os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
            }

            producer = Producer(conf)
            topic = os.getenv("KAFKA_TOPIC", "sensor_data")

            # Reset retry count on successful connection
            retry_count = 0

            logger.info(
                f"Starting Kafka producer, streaming to topic '{topic}'...",
                extra={"correlation_id": "N/A"},
            )

            try:
                while True:
                    correlation_id = str(uuid.uuid4())
                    data = get_sample_data()

                    try:
                        avro_bytes = serialize_avro(data, parsed_schema)
                        # Use sensor_id as key for partitioning
                        producer.produce(
                            topic,
                            key=str(data["sensor_id"]),
                            value=avro_bytes,
                            callback=lambda err,
                            msg,
                            cid=correlation_id: delivery_report(err, msg, cid),
                        )
                        # Poll more frequently to handle callbacks
                        producer.poll(0.1)
                    except BufferError:
                        logger.warning(
                            "Local buffer full, waiting for free space...",
                            extra={"correlation_id": correlation_id},
                        )
                        # Poll until space becomes available
                        producer.poll(1)
                        continue
                    except Exception as e:
                        logger.error(
                            f"Error producing message: {e}",
                            extra={"correlation_id": correlation_id},
                        )

                    time.sleep(1)  # Stream data every second
            except KeyboardInterrupt:
                logger.info(
                    "Producer stopped by user.", extra={"correlation_id": "N/A"}
                )
                break
            finally:
                # Ensure all messages are sent before exiting
                logger.info("Flushing producer...", extra={"correlation_id": "N/A"})
                producer.flush(10)  # 10 second timeout

        except Exception as e:
            retry_count += 1
            wait_time = min(30, 2**retry_count)  # Exponential backoff
            logger.error(
                f"Failed to initialize producer (attempt {retry_count}/{max_retries}): {e}. "
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


if __name__ == "__main__":
    main()
