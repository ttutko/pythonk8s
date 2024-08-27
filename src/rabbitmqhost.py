from typing import Optional
import logging
import time
import pika
import threading
import json
from pika.adapters.blocking_connection import BlockingConnection
from pika.adapters.blocking_connection import BlockingChannel

class RabbitMQHost:
    def __init__(self, cancel_event: threading.Event | None = None):
        self.connection: Optional[BlockingConnection] = None
        self.channel: Optional[BlockingChannel] = None
        self.logger = logging.getLogger(__name__)
        self.cancel_event = cancel_event

    def connect(self, amqpurl: str):
        rabbitmqserver = pika.URLParameters(amqpurl)
        self.connection = BlockingConnection(rabbitmqserver)
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange="test", exchange_type="topic")
        self.channel.queue_declare(queue="testqueue")
        self.channel.queue_bind(exchange="test", queue="testqueue", routing_key="test")
        self.channel.basic_consume(on_message_callback=self.message_handler,queue="testqueue",auto_ack=True)

        if self.cancel_event is not None:
            self.check_continue()

        self.channel.start_consuming()

    def message_handler(self, ch, method, properties, body):
        self.logger.warning(f"Message received: {body}")
        decoded_body = body.decode('utf-8')
        messsage = json.loads(decoded_body)

        if message['action'] == 'deploy':
            pass


    def cleanup(self):
        self.connection.close()

    def check_continue(self):
        if self.cancel_event and self.cancel_event.is_set():
            # self.logger.info("Cancelation requested, sleeping....")
            self.connection.add_callback_threadsafe(self.cleanup)
            # self.channel.stop_consuming()
        else:
            threading.Timer(5, self.check_continue).start()
