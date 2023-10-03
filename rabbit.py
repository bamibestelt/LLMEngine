import json
import os

import pika
from dotenv import load_dotenv
from langchain.document_loaders import AsyncHtmlLoader

from persistence import persist_blog_data, parse_blog_document
from privateGPT import PrivateGPT

load_dotenv()

RABBIT_HOST = os.environ.get('RABBIT_HOST')

# rss blog links channel
BLOG_LINKS_REQUEST = os.environ.get('BLOG_REQUEST_QUEUE')
BLOG_LINKS_REPLY = os.environ.get('BLOG_REPLY_QUEUE')
BLOG_RSS = os.environ.get('BLOG_RSS')

# prompt communication channels
PROMPT_QUEUE = os.environ.get('PROMPT_QUEUE')
LLM_REPLY_QUEUE = os.environ.get('LLM_REPLY_QUEUE')
LLM_UPDATE_QUEUE = os.environ.get('LLM_UPDATE_QUEUE')
LLM_STATUS_QUEUE = os.environ.get('LLM_STATUS_QUEUE')


def send_message(message: str, queue: str):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=queue)
    channel.basic_publish(exchange='', routing_key=queue, body=message)
    print(f"message {message} is sent to {queue}")
    channel.close()
    connection.close()


# listen to data update request.
# if a signal is captured, then it will send signal to processors
# it will wait for processors' reply and data
# ingest the data and keep updating the status to client
# channels: LLM_UPDATE_QUEUE & LLM_STATUS_QUEUE
def start_listen_data_update_request():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=LLM_UPDATE_QUEUE)
    channel.basic_consume(queue=LLM_UPDATE_QUEUE, on_message_callback=data_update_request_receiver, auto_ack=True)
    print('Listening to data-update request...')
    channel.start_consuming()


def data_update_request_receiver(channel, method, properties, body):
    request = body.decode('utf-8')
    print(f"data-update request: {request}")
    channel.stop_consuming()
    send_message('start', LLM_STATUS_QUEUE)
    # start listening to blog rss processor
    start_blog_links_request()
    # start listening to other processors
    # todo reply status to api middleware


# send data update status to client
# send data request to blog rss processor
# listening to reply
def start_blog_links_request():
    send_message('get-rss', LLM_STATUS_QUEUE)

    send_message(BLOG_RSS, BLOG_LINKS_REQUEST)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=BLOG_LINKS_REPLY)
    channel.basic_consume(queue=BLOG_LINKS_REPLY, on_message_callback=blog_links_receiver, auto_ack=True)
    print('Listening to blog rss reply...')
    channel.start_consuming()


def blog_links_receiver(channel, method, properties, body):
    print(f"Processor: {channel}. data: {body}")
    bytes_to_string = body.decode('utf-8')
    links = json.loads(bytes_to_string)
    print(f"Links data received: {len(links)}")
    docs = parse_blog_document(links)
    persist_blog_data(docs)
    channel.stop_consuming()

    send_message('finish', LLM_STATUS_QUEUE)


def start_listen_prompt():
    # need to add broker credentials
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=PROMPT_QUEUE)
    channel.basic_consume(queue=PROMPT_QUEUE, on_message_callback=prompt_receiver, auto_ack=True)
    print('Listening to prompt. To exit press CTRL+C')
    channel.start_consuming()


def prompt_receiver(channel, method, properties, body):
    prompt = body.decode('utf-8')
    print(f"Prompt received: {prompt}")
    answer_model = PrivateGPT().qa_prompt(prompt)
    json_model = json.dumps(answer_model, default=lambda o: o.__dict__, indent=4)
    send_message(json_model, LLM_REPLY_QUEUE)
    print('LLM reply sent')
