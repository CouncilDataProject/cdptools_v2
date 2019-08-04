FROM ubuntu:18.04

RUN apt-get update && apt-get upgrade -y 

RUN apt-get install -y \
    software-properties-common \
    default-jdk

RUN add-apt-repository universe

RUN apt-get update && apt-get install -y \
    ffmpeg \
    python3.7 \
    python3.7-dev \
    python3-pip

ENV JAVA_HOME="/usr/bin/java"

WORKDIR /home/
