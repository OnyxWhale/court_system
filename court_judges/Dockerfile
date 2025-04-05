FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
COPY --from=builder /root/.local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /root/.local/bin/ /usr/local/bin/
COPY . .

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN useradd -m -r appuser && chown -R appuser:appuser /app
USER appuser