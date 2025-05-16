from fastapi import FastAPI, HTTPException, Depends, Request, status
from pydantic import BaseModel, ValidationError, Field, validator
from confluent_kafka import Producer
import databases
import logging
import os
import uuid
import time
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from datetime import datetime


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
logger = logging.getLogger("fastapi_backend")
logger.addFilter(CorrelationIDFilter())

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
    sensor_id: int = Field(..., gt=0, description="Unique identifier for the sensor")
    temperature: float = Field(
        ..., ge=-50.0, le=100.0, description="Temperature reading in Celsius"
    )
    humidity: float = Field(..., ge=0.0, le=100.0, description="Humidity percentage")
    timestamp: int = Field(..., description="Unix timestamp of the reading")

    @validator("timestamp")
    def validate_timestamp(cls, v):
        # Ensure timestamp is not in the future
        if v > int(time.time()) + 60:  # Allow 1 minute clock skew
            raise ValueError("Timestamp cannot be in the future")
        return v


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


@app.post("/send", status_code=status.HTTP_202_ACCEPTED, response_model=dict)
async def send_data(
    data: SensorData,
    correlation_id: str = Depends(get_correlation_id),
    username: str = Depends(authenticate),
):
    try:
        # Convert to JSON string
        json_data = data.json()

        # Add retry logic for producing messages
        max_retries = 3
        for attempt in range(max_retries):
            try:
                producer.produce(
                    topic,
                    key=str(data.sensor_id),
                    value=json_data,
                    # Add timestamp for message ordering
                    timestamp=data.timestamp,
                )
                # Poll to handle delivery callbacks
                producer.poll(0)
                break
            except BufferError:
                # Local buffer full, wait and retry
                logger.warning(
                    f"Producer buffer full, waiting (attempt {attempt + 1}/{max_retries})",
                    extra={"correlation_id": correlation_id},
                )
                # Poll until space becomes available
                producer.poll(1.0)
                if attempt == max_retries - 1:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Service temporarily unavailable, please try again later",
                    )

        # Flush with timeout to ensure delivery
        producer.flush(timeout=5.0)

        logger.info(
            f"Sent data to Kafka: {json_data}",
            extra={"correlation_id": correlation_id},
        )

        return {
            "message": "Data sent to Kafka successfully",
            "sensor_id": data.sensor_id,
            "timestamp": data.timestamp,
        }
    except Exception as e:
        logger.error(
            f"Failed to send data to Kafka: {e}",
            extra={"correlation_id": correlation_id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send data to Kafka: {str(e)}",
        )


class SensorDataResponse(BaseModel):
    sensor_id: int
    temperature: float
    humidity: float
    timestamp: int
    # Add a human-readable timestamp for frontend display
    readable_time: Optional[str] = None

    @validator("readable_time", always=True)
    def set_readable_time(cls, v, values):
        if "timestamp" in values:
            return datetime.fromtimestamp(values["timestamp"]).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        return None


@app.get("/receive", response_model=List[SensorDataResponse])
async def receive_data(
    limit: int = 10,
    sensor_id: Optional[int] = None,
    min_temp: Optional[float] = None,
    max_temp: Optional[float] = None,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    correlation_id: str = Depends(get_correlation_id),
    username: str = Depends(authenticate),
):
    try:
        # Input validation
        if limit <= 0 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 100",
            )

        # Build query with filters
        query = "SELECT sensor_id, temperature, humidity, timestamp FROM sensor_data WHERE 1=1"
        values = {"limit": limit}

        if sensor_id is not None:
            query += " AND sensor_id = :sensor_id"
            values["sensor_id"] = sensor_id

        if min_temp is not None:
            query += " AND temperature >= :min_temp"
            values["min_temp"] = min_temp

        if max_temp is not None:
            query += " AND temperature <= :max_temp"
            values["max_temp"] = max_temp

        if start_time is not None:
            query += " AND timestamp >= :start_time"
            values["start_time"] = start_time

        if end_time is not None:
            query += " AND timestamp <= :end_time"
            values["end_time"] = end_time

        query += " ORDER BY timestamp DESC LIMIT :limit"

        # Execute query
        rows = await database.fetch_all(query=query, values=values)

        logger.info(
            f"Fetched {len(rows)} rows from database with filters",
            extra={"correlation_id": correlation_id},
        )

        # Convert to response model
        result = [dict(row) for row in rows]
        return result

    except ValidationError as ve:
        logger.error(
            f"Validation error: {ve}",
            extra={"correlation_id": correlation_id},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request parameters: {str(ve)}",
        )
    except Exception as e:
        logger.error(
            f"Failed to fetch data from database: {e}",
            extra={"correlation_id": correlation_id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch data from database",
        )
