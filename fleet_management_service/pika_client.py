import pika
import aio_pika
import os
import json


class PikaClient:
    def __init__(self):
        connection_parameters = pika.ConnectionParameters(
            os.environ.get('RABBITMQ_HOST')
        )
        self.connection = pika.BlockingConnection(connection_parameters)
        self.channel = self.connection.channel()

    async def consume(self, loop, consumer_handler):
        self.consumer_handler = consumer_handler
        connection = await aio_pika.connect_robust(
            host=os.environ.get('RABBITMQ_HOST'),
            port=5672,
            loop=loop
        )
        channel = await connection.channel()
        queue = await channel.declare_queue(
            os.environ.get('RECEIVE_POINTS_QUEUE'),
            durable=True,
            exclusive=False,
            auto_delete=False
        )
        await queue.consume(self.process_incoming_message)

        return connection

    async def process_incoming_message(self, message):
        body = message.body
        await message.ack()
        await self.consumer_handler(json.loads(body))

    def send_message(self, message):
        publish_properties = pika.BasicProperties(
            delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
        )
        self.channel.queue_declare(
            os.environ.get("SEND_TRIP_DATA_QUEUE"),
            durable=True,
            exclusive=False,
            auto_delete=False
        )
        self.channel.basic_publish(
            exchange='',
            routing_key=os.environ.get("SEND_TRIP_DATA_QUEUE"),
            body=json.dumps(message),
            properties=publish_properties
        )


pika_client = PikaClient()
