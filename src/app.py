import atexit
import logging
from threading import Thread, Event
from flask import Flask, appcontext_tearing_down
from src.rabbitmqhost import RabbitMQHost

logger = logging.getLogger(__name__)
logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.INFO)

cancel_consumer_event = Event()

app = Flask(__name__)

connection = RabbitMQHost(cancel_consumer_event)

_rabbit_thread = Thread(target=connection.connect, args=['amqp://guest:guest@localhost:30002'])
_rabbit_thread.start()

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

def shutdown_rabbitmq():
    logger.info('In shutdown...')
    if _rabbit_thread.is_alive():
        logger.info('Thread is alive, shutting down!')
        cancel_consumer_event.set()
        _rabbit_thread.join(timeout=30)
        if _rabbit_thread.is_alive():
            logger.warning("Thread still alive after timeout! Will forcibly exit now.")

# appcontext_tearing_down.connect(shutdown_rabbitmq, app)

atexit.register(shutdown_rabbitmq)
