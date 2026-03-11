FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 appuser  \
    && chown -R appuser:appuser /app

USER appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ../apps/new_services/*.py .
