FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY faust_app.py .

CMD ["python", "faust_app.py", "worker"]