import faust
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("faust_app")

app = faust.App(
    "sensor-stream-app", broker="kafka://localhost:9092", value_serializer="raw"
)

topic = app.topic("sensor_data", value_type=bytes)


class SensorData(faust.Record, serializer="json"):
    sensor_id: int
    temperature: float
    humidity: float
    timestamp: int


processed_topic = app.topic("processed_sensor_data", value_type=SensorData)


@app.agent(topic)
async def process_sensor_data(stream):
    async for event in stream:
        # Deserialize Avro bytes to dict
        # For simplicity, assume event is JSON string here; in real case, deserialize Avro
        # Here we just log and forward the event
        logger.info(f"Processing event: {event}")
        # Forward event to processed topic
        await processed_topic.send(value=event)


if __name__ == "__main__":
    app.main()
