# Data Streaming Project with Python and Apache Kafka

## Overview
This project demonstrates a real-time data streaming pipeline using Python, Apache Kafka, Faust stream processing, and PostgreSQL. It includes a Kafka producer that streams Avro-serialized sensor data, a Faust app for real-time stream processing, and a Kafka consumer that writes processed data to PostgreSQL.

## Prerequisites
- Python 3.7 or higher
- Docker and Docker Compose installed
- Kafka, Zookeeper, and PostgreSQL (can be run via Docker Compose)
- pip for Python package management

## Setup Instructions

### 1. Start Services with Docker Compose
From the project directory, run:
```
docker-compose up -d
```
This will start Zookeeper, Kafka, PostgreSQL, the FastAPI backend, and the React frontend.

### 2. Install Python dependencies
Run:
```
pip install -r requirements.txt
```

### 3. Run the Kafka Producer
This script streams Avro-serialized sensor data to the Kafka topic `sensor_data`.
```
python producer.py
```

### 4. Run the Faust Stream Processing App
This app processes data from `sensor_data` topic and forwards to `processed_sensor_data`.
```
faust -A faust_app worker -l info
```

### 5. Run the Kafka Consumer
This script consumes data from `sensor_data` and writes to PostgreSQL.
```
python consumer.py
```

### 6. Run the FastAPI Backend
From the backend directory, run:
```
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 7. Run the React Frontend
From the frontend directory, run:
```
npm start
```
uvicorn main:app --host 0.0.0.0 --port 8000
This script consumes data from `sensor_data` and writes to PostgreSQL.
This app processes data from `sensor_data` topic and forwards to `processed_sensor_data`.

## Notes
- Kafka topics `sensor_data` and `processed_sensor_data` are created automatically by Docker Compose.
- Update database connection details in `consumer.py` if needed.
- Customize data generation in `producer.py` and processing logic in `faust_app.py`.
- Use Docker Compose to manage service lifecycle.

## References
- [Kafka Python Client](https://kafka-python.readthedocs.io/en/master/)
- [Faust Stream Processing](https://faust.readthedocs.io/en/latest/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Docker Compose](https://docs.docker.com/compose/)
