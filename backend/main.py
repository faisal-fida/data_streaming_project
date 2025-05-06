from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel, ValidationError
from confluent_kafka import Producer
import asyncio
import databases
import json
import logging
import os
import uuid
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(correlation_id)s] %(message)s",
)
logger = logging.getLogger("fastapi_backend")

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost/sensor_db"
)
database = databases.Database(DATABASE_URL)

app = FastAPI()

# Security: Basic HTTP Auth placeholder
security = HTTPBasic()

# Add CORS middleware for security best practices
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("FRONTEND_URL", "http://localhost:3000")
    ],  # Restrict to frontend URL
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

producer_conf = {
    "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
}
producer = Producer(producer_conf)
topic = os.getenv("KAFKA_TOPIC", "sensor_data")


class SensorData(BaseModel):
    sensor_id: int
    temperature: float
    humidity: float
    timestamp: int


async def get_correlation_id(request: Request):
    return str(uuid.uuid4())


async def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    # Placeholder authentication logic
    correct_username = os.getenv("API_USERNAME", "admin")
    correct_password = os.getenv("API_PASSWORD", "password")
    if (
        credentials.username != correct_username
        or credentials.password != correct_password
    ):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return credentials.username


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.post("/send")
async def send_data(
    data: SensorData,
    correlation_id: str = Depends(get_correlation_id),
    username: str = Depends(authenticate),
):
    try:
        producer.produce(topic, key=str(data.sensor_id), value=data.json())
        producer.flush()
        logger.info(
            f"Sent data to Kafka: {data.json()}",
            extra={"correlation_id": correlation_id},
        )
        return {"message": "Data sent to Kafka successfully"}
    except Exception as e:
        logger.error(
            f"Failed to send data to Kafka: {e}",
            extra={"correlation_id": correlation_id},
        )
        raise HTTPException(status_code=500, detail="Failed to send data to Kafka")


@app.get("/receive")
async def receive_data(
    limit: int = 10,
    correlation_id: str = Depends(get_correlation_id),
    username: str = Depends(authenticate),
):
    try:
        query = "SELECT sensor_id, temperature, humidity, timestamp FROM sensor_data ORDER BY timestamp DESC LIMIT :limit"
        rows = await database.fetch_all(query=query, values={"limit": limit})
        logger.info(
            f"Fetched {len(rows)} rows from database",
            extra={"correlation_id": correlation_id},
        )
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(
            f"Failed to fetch data from database: {e}",
            extra={"correlation_id": correlation_id},
        )
        raise HTTPException(
            status_code=500, detail="Failed to fetch data from database"
        )
