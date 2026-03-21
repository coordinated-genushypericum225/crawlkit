FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y wget gnupg && rm -rf /var/lib/apt/lists/*

# Cache buster
ARG CACHEBUST=1

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Playwright
RUN playwright install chromium && playwright install-deps chromium

# App
COPY crawlkit/ crawlkit/
COPY database/ database/
COPY pyproject.toml .

ENV PORT=8080
ENV CRAWLKIT_MASTER_KEY=""
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["python", "-m", "uvicorn", "crawlkit.api.server:app", "--host", "0.0.0.0", "--port", "8080"]
