from typing import Optional
import logging
import time
import pika
import threading
import json
from pika.adapters.blocking_connection import BlockingConnection
from pika.adapters.blocking_connection import BlockingChannel
from kubernetes import client, config

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
        self.channel.basic_consume(on_message_callback=self.message_handler,queue="testqueue",auto_ack=False)

        if self.cancel_event is not None:
            self.check_continue()

        self.channel.start_consuming()

    def message_handler(self, ch, method, properties, body):
        self.logger.warning(f"Message received: {body}")
        decoded_body = body.decode('utf-8')
        message = json.loads(decoded_body)
        self.logger.error("Recieved a message!")

        if message['action'] == 'deploy':
            self.handle_deploy(message, ch, method, properties, body) 


    def cleanup(self):
        self.connection.close()
        self.logger.info("Connection Closed.")

    def check_continue(self):
        if self.cancel_event and self.cancel_event.is_set():
            self.logger.info("Cancelation requested....")
            self.connection.add_callback_threadsafe(self.cleanup)
            # self.channel.stop_consuming()
        else:
            threading.Timer(5, self.check_continue).start()

    def handle_deploy(self, message, ch, method, properties, body):
        self.logger.info("Recieved deploy message")

        if "image" in message:
            self.logger.info(f"Image: {message['image']}")
        else:
            self.logger.warn(f"No Image Provided!")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        replicas = message['replicas']

        config.load_kube_config()
        v1 = client.CoreV1Api()
        dep_container = client.V1Container(
                name="nginx",
                image=message['image'],
                ports=[client.V1ContainerPort(container_port=80)],
                resources=client.V1ResourceRequirements(
                    requests={"cpu":"100m", "memory":"200Mi"},
                    limits={"cpu":"500m", "memory":"500Mi"})
        )
        template = client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={"app": "myclient"}),
                spec = client.V1PodSpec(containers=[dep_container])
        )

        dep_spec=client.V1DeploymentSpec(
                replicas=replicas,
                template=template,
                selector={
                    "matchLabels": {"app":"myclient"}
                }
        )
        deployment=client.V1Deployment(
                api_version="apps/v1",
                kind="Deployment",
                metadata=client.V1ObjectMeta(name="my-deployment", namespace="dev"),
                spec=dep_spec
        )

        namespace=client.V1Namespace()
        namespace.metadata=client.V1ObjectMeta(name="dev")
        v1.replace_namespace(name="dev", body=namespace)
        apps_v1 = client.AppsV1Api()
        resp = apps_v1.create_namespaced_deployment(
                body=deployment,
                namespace="dev"
        )

        self.logger.info(resp)



        ch.basic_ack(delivery_tag=method.delivery_tag)
