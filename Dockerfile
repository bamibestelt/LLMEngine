# Use the latest version of Ubuntu as a parent image
FROM python:3.11.4

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# upgrade pip
RUN pip3 install --upgrade pip

# install everything in requirements.txt except gpt4all which has problem
RUN pip install --no-cache-dir -r requirements.txt

# install gpt4all manually
# RUN pip install gpt4all-1.0.8-py3-none-manylinux1_x86_64.whl

# Make port 80 available to the world outside this container
EXPOSE 80

# Run main.py when the container launches
CMD ["python3", "main.py"]