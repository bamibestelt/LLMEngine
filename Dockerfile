# Use the latest version of Ubuntu as a parent image
FROM ubuntu:latest

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

WORKDIR /

# Update the system
RUN apt-get update -y
# Install dependencies for building Python
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y build-essential wget libffi-dev libgdbm-dev libc6-dev libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev libncurses5-dev libncursesw5-dev xz-utils tk-dev
# Download and extract Python 3.11.0
RUN wget https://www.python.org/ftp/python/3.11.0/Python-3.11.0.tgz
RUN tar -xvf Python-3.11.0.tgz
# Change to the Python source directory
WORKDIR Python-3.11.0
# Configure and build Python
RUN ./configure --enable-optimizations
RUN make -j$(nproc)

# Install Python
RUN make altinstall

# install pip
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# upgrade pip
RUN pip3 install --upgrade pip

WORKDIR /app

# install everything in requirements.txt except gpt4all which has problem
RUN pip install --no-cache-dir -r requirements.txt

# install gpt4all manually
RUN pip install gpt4all-1.0.8-py3-none-manylinux1_x86_64.whl

# Make port 80 available to the world outside this container
EXPOSE 80

# Run main.py when the container launches
CMD ["python3", "main.py"]