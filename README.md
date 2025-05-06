# Real-Time Data Streaming Project

## Overview
This project demonstrates a real-time data streaming pipeline using Python, Apache Kafka, Faust stream processing, and PostgreSQL. It includes a React frontend for data visualization and interaction, a FastAPI backend for API endpoints, and a complete data pipeline for sensor data processing.

### Architecture
```
┌─────────────┐    ┌─────────┐    ┌──────────────┐    ┌────────────┐
│   Producer  │───▶│  Kafka  │───▶│  Faust App   │───▶│ Processed  │
│  (sensor    │    │ Topic:  │    │ (real-time   │    │   Topic    │
│   data)     │    │sensor_data│   │ processing)  │    │            │
└─────────────┘    └─────────┘    └──────────────┘    └────────────┘
                        │                                    │
                        ▼                                    │
                  ┌──────────┐                              │
                  │ Consumer │◀───────────────────────────┘
                  │          │
                  └──────────┘
                        │
                        ▼
                  ┌──────────┐    ┌─────────────┐    ┌─────────────┐
                  │PostgreSQL│◀───│  FastAPI    │◀───│    React    │
                  │ Database │    │  Backend    │    │  Frontend   │
                  └──────────┘    └─────────────┘    └─────────────┘
```

## Features
- **Kafka Producer**: Generates and streams Avro-serialized sensor data
- **Faust Stream Processing**: Real-time data transformation and processing
- **Kafka Consumer**: Consumes and stores data in PostgreSQL
- **FastAPI Backend**: RESTful API with authentication and data validation
- **React Frontend**: Interactive dashboard for data visualization and management
- **Docker Support**: Containerized deployment for all components
- **Error Handling**: Robust error handling and retry mechanisms
- **Logging**: Structured logging with correlation IDs for traceability

## Prerequisites
- Docker and Docker Compose (recommended for easy setup)
- Python 3.9 or higher (if running components locally)
- Node.js 18+ (if running frontend locally)
- Kafka and Zookeeper (included in Docker Compose)
- PostgreSQL (included in Docker Compose)

## Quick Start with Docker

The easiest way to run the entire application is using Docker Compose:

```bash
# Clone the repository
git clone <repository-url>
cd data_streaming_project

# Start all services
docker-compose up -d

# Check service status
docker-compose ps
```

The services will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Kafka: localhost:9092
- PostgreSQL: localhost:5432

## Manual Setup (Development)

### 1. Set up environment variables
Create a `.env` file in the project root with the following variables:
```
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC=sensor_data
PROCESSED_KAFKA_TOPIC=processed_sensor_data
POSTGRES_HOST=localhost
POSTGRES_DB=sensor_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
API_USERNAME=admin
API_PASSWORD=password
FRONTEND_URL=http://localhost:3000
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
pip install -r backend/requirements.txt
```

### 3. Install Frontend dependencies
```bash
cd frontend
npm install
cd ..
```

### 4. Start Kafka and PostgreSQL
```bash
docker-compose up -d zookeeper kafka postgres
```

### 5. Run the components
In separate terminal windows:

```bash
# Run the producer
python producer.py

# Run the Faust app
faust -A faust_app worker -l info

# Run the consumer
python consumer.py

# Run the backend
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Run the frontend
cd frontend
npm start
```

## API Endpoints

### Authentication
All API endpoints use HTTP Basic Authentication:
- Username: `admin` (default, configurable via environment)
- Password: `password` (default, configurable via environment)

### Send Data
```
POST /send
```
Request body:
```json
{
  "sensor_id": 1,
  "temperature": 25.5,
  "humidity": 45.2,
  "timestamp": 1617293932
}
```

### Receive Data
```
GET /receive?limit=10&sensor_id=1&min_temp=20&max_temp=30
```
Query parameters:
- `limit`: Maximum number of records to return (default: 10)
- `sensor_id`: Filter by sensor ID (optional)
- `min_temp`: Minimum temperature (optional)
- `max_temp`: Maximum temperature (optional)
- `start_time`: Start timestamp (optional)
- `end_time`: End timestamp (optional)

## Component Details

### Producer
The producer generates simulated sensor data and sends it to Kafka using Avro serialization. It includes:
- Configurable data generation
- Robust error handling and retry logic
- Structured logging with correlation IDs

### Faust App
The Faust app processes the raw sensor data stream in real-time:
- Deserializes Avro data
- Performs data validation and transformation
- Forwards processed data to a new Kafka topic

### Consumer
The consumer reads data from Kafka and stores it in PostgreSQL:
- JSON schema validation
- Database connection management with retry logic
- Error handling for various failure scenarios

### Backend
The FastAPI backend provides RESTful API endpoints:
- Data validation using Pydantic models
- Authentication and authorization
- Database access via async database connections
- Kafka integration for producing messages

### Frontend
The React frontend provides a user interface for:
- Sending sensor data to Kafka
- Viewing and filtering stored sensor data
- Real-time data updates with auto-refresh
- Form validation and error handling

## Troubleshooting

### Common Issues

1. **Kafka Connection Issues**
   - Ensure Kafka and Zookeeper are running: `docker-compose ps`
   - Check Kafka logs: `docker-compose logs kafka`
   - Verify the bootstrap servers configuration matches your environment

2. **Database Connection Issues**
   - Ensure PostgreSQL is running: `docker-compose ps`
   - Check database logs: `docker-compose logs postgres`
   - Verify database credentials in environment variables

3. **Frontend/Backend Connection Issues**
   - Check that the API_BASE_URL in the frontend matches your backend URL
   - Ensure CORS is properly configured in the backend
   - Verify network connectivity between services

### Logs
Check the logs for detailed error information:
```bash
# View logs for all services
docker-compose logs

# View logs for a specific service
docker-compose logs backend
```

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## References
- [Confluent Kafka Python Client](https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html)
- [Faust Stream Processing](https://faust.readthedocs.io/en/latest/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://reactjs.org/docs/getting-started.html)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Docker Compose](https://docs.docker.com/compose/)
