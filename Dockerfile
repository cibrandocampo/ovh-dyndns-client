## Stage 1 - Install requirements ##
FROM python:3.14-alpine AS base

WORKDIR /install

# Install build dependencies for cryptography/cffi
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    rust

RUN pip install --upgrade pip \
    && mkdir -p /install/wheels

COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /install/wheels -r requirements.txt

## Stage 2 - Image creation ##
FROM python:3.14-alpine

WORKDIR /app

# Install runtime dependencies
RUN apk add --no-cache libffi openssl \
    && mkdir -p /app/data

COPY --from=base /install/wheels /wheels
RUN pip install --no-cache /wheels/* && rm -r /wheels

COPY ./src /app

# Expose API port
EXPOSE 8000

ENTRYPOINT ["python", "main.py"]
