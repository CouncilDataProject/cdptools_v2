#!/bin/sh

apt-get update
apt-get install software-properties-common -y
apt-get install default-jdk -y
apt-get install python3-pip -y
export JAVA_HOME="/usr/bin/java"
