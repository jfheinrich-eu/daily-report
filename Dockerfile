FROM python:3.12.11-alpine3.22

# Copy source code
COPY src/ ./src/

# Install dependencies
COPY pyproject.toml poetry.lock* ./

RUN pip install poetry && poetry install --no-interaction --no-ansi --no-root --only main

WORKDIR /src

# Set entrypoint
ENTRYPOINT ["python", "-m", "daily_report.main"]
