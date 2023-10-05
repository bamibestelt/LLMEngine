# Use the latest version of Ubuntu as a parent image
FROM ubuntu:latest

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app
COPY .env /app/.env
COPY .venv /venv

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

WORKDIR /app

# include some other path into your site-packages
ADD libs.pth /usr/local/lib/python3.11/site-packages/libs.pth

# Make port 80 available to the world outside this container
EXPOSE 80

# test

# Run main.py when the container launches
CMD ["python3.11", "main.py"]