FROM python:3.12.11-alpine3.22@sha256:c610e4a94a0e8b888b4b225bfc0e6b59dee607b1e61fb63ff3926083ff617216

# Copy source code
COPY src/ ./src/

# Install dependencies
COPY pyproject.toml poetry.lock* ./

RUN pip install poetry && poetry install --no-interaction --no-ansi --no-root --only main

WORKDIR /src

# Set entrypoint
ENTRYPOINT ["python", "-m", "daily_report.main"]
