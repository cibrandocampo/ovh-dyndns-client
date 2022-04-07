FROM python:3.10-slim

# Enviroment variables
ENV API_PUBLIC_IP_URL=https://api.ipify.org
ENV PUBLIC_IP_FILE_PATH=/tmp/current_ip
ENV DOMAINS_CONFIG_FILE_PATH=/dyndns-client/config/domains.json
ENV UPDATE_INTERVAL=300

# Create directories & copy code
RUN mkdir /dyndns-client
WORKDIR /dyndns-client

# Installing dependencies
COPY install/requirements /dyndns-client/
RUN pip install --upgrade pip && pip install -r requirements && rm requirements

# Copy code
COPY code/ /dyndns-client

CMD ["python", "/dyndns-client/client.py"]
