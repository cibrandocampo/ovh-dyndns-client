FROM python:3.14-alpine

# Update pip
RUN pip install --upgrade pip

COPY dev-requirements.txt .

RUN pip install -r dev-requirements.txt
