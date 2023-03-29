FROM python:3.9-alpine

WORKDIR /src
RUN pip install websockets
COPY requirements.txt /src
RUN pip install -r requirements.txt
COPY . /src