FROM ubuntu

# General upgrades and requirements
RUN apt-get update && apt-get upgrade -y

# Get software props
RUN apt-get install -y \
    software-properties-common \
    default-jdk

# Add additional apt repository
RUN add-apt-repository universe

# Get python3.8 and pip
RUN apt-get update && apt-get install -y \
    python3.8 \
    python3.8-dev \
    python3-pip \
    ffmpeg \
    git

# Upgrade pip and force it to use python3.8
RUN python3.8 -m pip install --upgrade pip

# Set python3.8 to default python
RUN ln -sf /usr/bin/python3.8 /usr/bin/python
RUN ln -sf /usr/bin/python3.8 /usr/bin/python3
RUN ln -sf /usr/bin/pip3 /usr/bin/pip

# Upgrade pip
RUN pip install --upgrade pip

# Set java home
ENV JAVA_HOME="/usr/bin/java"

# Clone CDP and checkout new branch
RUN git clone https://github.com/CouncilDataProject/cdptools.git
WORKDIR cdptools/
RUN git checkout feature/update-index-pipeline
RUN pip install .[seattle]

# Set working directory
WORKDIR /home/
