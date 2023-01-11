# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt
RUN \
    apt-get update \
    && apt-get -y install libpq-dev gcc \
    && pip3 install -r requirements.txt
COPY /app .
CMD [ "python3", "run.py"]
