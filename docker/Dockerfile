FROM ubuntu:18.04

RUN apt-get update && apt-get install -y \
    software-properties-common

RUN add-apt-repository universe

RUN apt-get update && apt-get install -y \
    ffmpeg \
    python3.7 \
    python3.7-dev \
    python3-pip

WORKDIR /home/
