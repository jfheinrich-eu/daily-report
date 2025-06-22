FROM python:3.12-slim

# Update and upgrade to fix vulnerabilities
RUN apt-get update && apt-get upgrade -y && apt-get clean

WORKDIR /app

# Install dependencies
COPY pyproject.toml poetry.lock* ./
RUN pip install poetry && poetry install --no-interaction --no-ansi --only main

# Copy source code
COPY src/ ./src/

# Set entrypoint
ENTRYPOINT ["python", "-m", "daily_report.main"]