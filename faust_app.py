import faust
import logging
import os
import io
from fastavro import schemaless_reader, parse_schema
import uuid
import asyncio

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(correlation_id)s] %(message)s",
)
logger = logging.getLogger("faust_app")

# Avro schema for sensor data
schema = {
    "type": "record",
    "name": "SensorData",
    "fields": [
        {"name": "sensor_id", "type": "int"},
        {"name": "temperature", "type": "float"},
        {"name": "humidity", "type": "float"},
        {"name": "timestamp", "type": "int"},
    ],
}
parsed_schema = parse_schema(schema)

app = faust.App(
    "sensor-stream-app",
    broker=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka://localhost:9092"),
    value_serializer="raw",
)

topic = app.topic(os.getenv("KAFKA_TOPIC", "sensor_data"), value_type=bytes)


class SensorData(faust.Record, serializer="json"):
    sensor_id: int
    temperature: float
    humidity: float
    timestamp: int


processed_topic = app.topic(
    os.getenv("PROCESSED_KAFKA_TOPIC", "processed_sensor_data"), value_type=SensorData
)


@app.agent(topic)
async def process_sensor_data(stream):
    async for event in stream:
        correlation_id = str(uuid.uuid4())
        try:
            # Deserialize Avro bytes to dict
            bytes_reader = io.BytesIO(event)
            data = schemaless_reader(bytes_reader, parsed_schema)
            logger.info(
                f"Processing event: {data}", extra={"correlation_id": correlation_id}
            )

            # Add data validation
            if not all(
                k in data for k in ["sensor_id", "temperature", "humidity", "timestamp"]
            ):
                logger.warning(
                    f"Incomplete data received: {data}",
                    extra={"correlation_id": correlation_id},
                )
                continue

            sensor_data = SensorData(**data)
            # Forward event to processed topic
            await processed_topic.send(value=sensor_data)
            logger.info(
                f"Event forwarded to processed topic",
                extra={"correlation_id": correlation_id},
            )
        except ValueError as ve:
            logger.error(
                f"Data validation error: {ve}",
                extra={"correlation_id": correlation_id},
            )
        except Exception as e:
            logger.error(
                f"Failed to process event: {e}",
                extra={"correlation_id": correlation_id},
            )
            # Add a small delay before continuing to prevent tight error loops
            await asyncio.sleep(0.5)


if __name__ == "__main__":
    app.main()
