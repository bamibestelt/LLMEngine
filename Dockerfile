# Use the latest version of Ubuntu as a parent image
FROM python:3.11.4

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# upgrade pip
RUN pip3 install --upgrade pip

# install everything in requirements.txt except gpt4all which has problem
RUN pip3 install --no-cache-dir -r requirements.txt

# install gpt4all manually
# RUN pip install gpt4all-1.0.8-py3-none-macosx_10_9_universal2.whl

# file paths needed to be specified with volumes
ENV PERSIST_DIRECTORY=""
ENV MODEL_PATH=""

# environment variables
ENV MODEL_TYPE=GPT4All
ENV EMBEDDINGS_MODEL_NAME="all-MiniLM-L6-v2"
ENV MODEL_N_CTX=1000
ENV MODEL_N_BATCH=8
ENV TARGET_SOURCE_CHUNKS=4

ENV RABBIT_HOST="localhost"

# coda links channel
ENV CODA_REQUEST_QUEUE="coda.request"
ENV CODA_REPLY_QUEUE="coda.links"

# rss blog links channel
ENV BLOG_REQUEST_QUEUE="blog.request"
ENV BLOG_REPLY_QUEUE="blog.links"
ENV BLOG_RSS=""

# prompt communication channels
ENV PROMPT_QUEUE="prompt.queue"
ENV LLM_REPLY_QUEUE="llm.queue.reply"
ENV LLM_UPDATE_QUEUE="llm.queue.update"
ENV LLM_STATUS_QUEUE="llm.queue.status"

# Run main.py when the container launches
CMD ["python3", "main.py"]