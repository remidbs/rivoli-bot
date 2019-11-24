FROM python:3.7

RUN apt update
RUN apt install -y python3-numpy build-essential python-dev libxml2 libxml2-dev zlib1g-dev gfortran libatlas-base-dev libjpeg-dev libfreetype6-dev libpng-dev

WORKDIR /app


COPY . ./rivoli-bot
