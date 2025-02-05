## Stage 1 - Install requirements ##
FROM python:3.13-alpine AS base

WORKDIR /install

RUN pip install --upgrade pip \
    && mkdir -p /install/wheels

COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /install/wheels -r requirements.txt

## Stage 2 - Image creation ##
FROM python:3.13-alpine

WORKDIR /app

COPY --from=base /install/wheels /wheels
RUN pip install --no-cache /wheels/* && rm -r /wheels

COPY ./src /app

ENTRYPOINT ["python", "main.py"]
