## Stage 1 - Install requirements ##

FROM python:3.10-alpine as base

# Update pip
RUN pip install --upgrade pip

# Copy installation files
COPY ./install /install

# Install packages as wheels
RUN pip wheel --no-cache-dir --wheel-dir /install/wheels -r /install/requirements.txt



## Stage 2 - Image creation ##

FROM python:3.10-alpine

# Enviroment variables
ENV API_PUBLIC_IP_URL=https://api.ipify.org
ENV PUBLIC_IP_FILE_PATH=/tmp/current_ip
ENV DOMAINS_CONFIG_FILE_PATH=/dyndns-client/config/domains.json
ENV UPDATE_INTERVAL=300

# Install compiled packages
COPY --from=base /install/wheels /wheels
RUN pip install --upgrade pip && pip install --no-cache /wheels/* && rm -r /wheels

# Copy code
COPY code/ /dyndns-client

CMD ["python", "/dyndns-client/client.py"]
