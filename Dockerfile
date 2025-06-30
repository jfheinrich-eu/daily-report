FROM python:3.13.5-alpine3.22@sha256:9b4929a72599b6c6389ece4ecbf415fd1355129f22bb92bb137eea098f05e975 AS builder

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

FROM python:3.13.5-alpine3.22@sha256:9b4929a72599b6c6389ece4ecbf415fd1355129f22bb92bb137eea098f05e975 AS final
COPY --from=builder /app /app
WORKDIR /app
ENV PYTHONPATH=/app

# Set entrypoint
ENTRYPOINT ["python", "-m", "daily_report.main"]
