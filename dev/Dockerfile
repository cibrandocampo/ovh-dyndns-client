FROM python:3.14-alpine

# Update pip
RUN pip install --upgrade pip

# Install runtime requirements + dev-only requirements (both pinned with hashes)
COPY requirements.txt requirements.txt
COPY dev/requirements.txt requirements.dev.txt

RUN pip install --require-hashes -r requirements.txt -r requirements.dev.txt
