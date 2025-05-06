FROM python:3.9-slim AS builder

WORKDIR /app

# The COPY command should be relative to the build context
COPY requirements.txt .

RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.9-slim

WORKDIR /app

COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH

# Create a non-root user and switch to it
RUN addgroup --system appgroup && adduser --system appuser --ingroup appgroup
USER appuser

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
