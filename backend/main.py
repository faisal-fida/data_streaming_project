from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from confluent_kafka import Producer
import asyncio
import databases
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fastapi_backend")

DATABASE_URL = "postgresql://postgres:postgres@localhost/sensor_db"
database = databases.Database(DATABASE_URL)

app = FastAPI()

producer_conf = {"bootstrap.servers": "localhost:9092"}
producer = Producer(producer_conf)
topic = "sensor_data"


class SensorData(BaseModel):
    sensor_id: int
    temperature: float
    humidity: float
    timestamp: int


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.post("/send")
async def send_data(data: SensorData):
    try:
        producer.produce(topic, key=str(data.sensor_id), value=data.json())
        producer.flush()
        logger.info(f"Sent data to Kafka: {data.json()}")
        return {"message": "Data sent to Kafka successfully"}
    except Exception as e:
        logger.error(f"Failed to send data to Kafka: {e}")
        raise HTTPException(status_code=500, detail="Failed to send data to Kafka")


@app.get("/receive")
async def receive_data(limit: int = 10):
    query = "SELECT sensor_id, temperature, humidity, timestamp FROM sensor_data ORDER BY timestamp DESC LIMIT :limit"
    rows = await database.fetch_all(query=query, values={"limit": limit})
    return [dict(row) for row in rows]
