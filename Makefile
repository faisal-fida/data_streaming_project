.PHONY: setup install-deps run-producer run-consumer run-faust run-backend run-frontend run-all

# Setup virtual environment
setup:
	python -m venv venv
	@echo "Virtual environment created. Now run 'make install-deps' to install dependencies."

# Install dependencies
install-deps:
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install kafka-python fastavro psycopg2-binary faust jsonschema
	. venv/bin/activate && pip install fastapi uvicorn databases httpx
	. venv/bin/activate && pip install librdkafka
	. venv/bin/activate && pip install confluent-kafka
	cd backend && . ../venv/bin/activate && pip install fastapi uvicorn databases confluent-kafka
	cd frontend && npm install

# Run producer
run-producer:
	. venv/bin/activate && KAFKA_BOOTSTRAP_SERVERS=localhost:29092 KAFKA_TOPIC=sensor_data python producer.py

# Run consumer
run-consumer:
	. venv/bin/activate && KAFKA_BOOTSTRAP_SERVERS=localhost:29092 KAFKA_TOPIC=processed_sensor_data POSTGRES_HOST=localhost POSTGRES_DB=sensor_db POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres python consumer.py

# Run Faust app
run-faust:
	. venv/bin/activate && KAFKA_BOOTSTRAP_SERVERS=localhost:29092 KAFKA_TOPIC=sensor_data PROCESSED_KAFKA_TOPIC=processed_sensor_data python faust_app.py worker

# Run backend
run-backend:
	cd backend && . ../venv/bin/activate && DATABASE_URL=postgresql://postgres:postgres@localhost/sensor_db KAFKA_BOOTSTRAP_SERVERS=localhost:29092 API_USERNAME=admin API_PASSWORD=password uvicorn main:app --host 0.0.0.0 --port 8000

# Run frontend
run-frontend:
	cd frontend && npm start

# Run all services in separate terminals (requires tmux)
run-all:
	tmux new-session -d -s data_streaming "make run-producer"
	tmux split-window -h -t data_streaming "make run-faust"
	tmux split-window -v -t data_streaming "make run-consumer"
	tmux split-window -v -t data_streaming:0.0 "make run-backend"
	tmux split-window -v -t data_streaming:0.1 "make run-frontend"
	tmux attach-session -t data_streaming