import time
import random
from confluent_kafka import Producer
from fastavro import parse_schema, schemaless_writer
import io
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("producer")

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


def delivery_report(err, msg):
    if err is not None:
        logger.error(f"Message delivery failed: {err}")
    else:
        logger.info(f"Message delivered to {msg.topic()} [{msg.partition()}]")


def serialize_avro(data, schema):
    bytes_writer = io.BytesIO()
    schemaless_writer(bytes_writer, schema, data)
    return bytes_writer.getvalue()


def main():
    conf = {"bootstrap.servers": "localhost:9092"}
    producer = Producer(conf)
    topic = "sensor_data"

    logger.info(f"Starting Kafka producer, streaming to topic '{topic}'...")
    try:
        while True:
            data = get_sample_data()
            avro_bytes = serialize_avro(data, parsed_schema)
            # Use sensor_id as key for partitioning
            producer.produce(
                topic,
                key=str(data["sensor_id"]),
                value=avro_bytes,
                callback=delivery_report,
            )
            producer.poll(0)
            time.sleep(1)  # Stream data every second
    except KeyboardInterrupt:
        logger.info("Producer stopped.")
    finally:
        producer.flush()


if __name__ == "__main__":
    main()
