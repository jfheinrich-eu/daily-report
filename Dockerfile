FROM python:3.12.11-alpine3.22@sha256:c610e4a94a0e8b888b4b225bfc0e6b59dee607b1e61fb63ff3926083ff617216 AS builder

# Install dependencies
COPY pyproject.toml poetry.lock* /project/

# Copy source code
COPY src/ /project/src/

ADD src /app

WORKDIR /project

RUN pip install poetry && \
    poetry self add poetry-plugin-export && \
    poetry export --without-hashes -f requirements.txt -o /app/requirements.txt && \
    pip install --no-cache-dir --target /app -r /app/requirements.txt

FROM python:3.12.11-alpine3.22@sha256:c610e4a94a0e8b888b4b225bfc0e6b59dee607b1e61fb63ff3926083ff617216 AS final
COPY --from=builder /app /app
WORKDIR /app
ENV PYTHONPATH=/app

# Set entrypoint
ENTRYPOINT ["python", "-m", "daily_report.main"]
