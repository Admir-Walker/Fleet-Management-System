from dotenv import load_dotenv
import json
import os
import asyncio
import aio_pika
import random
from datetime import datetime
import calendar


load_dotenv()


async def publish(channel, body, queue_name):
    await channel.default_exchange.publish(
        aio_pika.Message(
            body=json.dumps(body).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        ),
        routing_key=queue_name
    )


def get_negative_or_positive():
    return 1 if random.random() < 0.5 else -1


def get_current_timestamp():
    utc_dt = datetime.utcnow()
    current_timetuple = utc_dt.utctimetuple()
    current_timestamp = calendar.timegm(current_timetuple)
    return current_timestamp


async def consumer_handler(message, sending_channel):
    send_gps_data_queue = os.environ.get("SEND_GPS_DATA_QUEUE")
    depature_geo_point = message.get("depature_geo_point", None)
    destination_geo_point = message.get("destination_geo_point", None)
    driver_id = message.get("driver_id", None)
    trip_id = message.get("trip_id", None)
    vehicle_id = message.get("vehicle_id", None)

    number_of_points = random.randint(5, 10)
    dep_lat, dep_long = depature_geo_point["lat"], depature_geo_point["long"]
    dest_lat, dest_long = destination_geo_point["lat"], destination_geo_point["long"]

    body = {
        "current_geo_point": {
            "lat": dep_lat,
            "long": dep_long
        },
        "speed": 0,
        "driver_id": driver_id,
        "trip_id": trip_id,
        "vehicle_id": vehicle_id,
        "timestamp": get_current_timestamp()
    }

    await publish(sending_channel, body, send_gps_data_queue)

    await asyncio.sleep(2)

    speed = random.randint(50, 120)

    for _ in range(1, number_of_points):
        dep_lat += \
            ((dep_lat + (get_negative_or_positive() * dest_lat)) / number_of_points)/10
        dep_long += \
            ((dep_long + (get_negative_or_positive() * dest_long)) /
             number_of_points)/10

        speed = speed + (get_negative_or_positive()) * random.randint(1, 5)

        body = {
            "current_geo_point": {
                "lat": dep_lat,
                "long": dep_long
            },
            "speed": speed,
            "driver_id": driver_id,
            "trip_id": trip_id,
            "vehicle_id": vehicle_id,
            "timestamp": get_current_timestamp()

        }
        await publish(sending_channel, body, send_gps_data_queue)
        await asyncio.sleep(2)

    dep_lat, dep_long = dest_lat, dest_long
    speed = 0

    body = {
        "current_geo_point": {
            "lat": dep_lat,
            "long": dep_long
        },
        "speed": 0,
        "driver_id": driver_id,
        "trip_id": trip_id,
        "vehicle_id": vehicle_id,
        "trip_finished": True,
        "timestamp": get_current_timestamp()

    }

    await publish(sending_channel, body, send_gps_data_queue)
    await asyncio.sleep(2)


async def main() -> None:
    connection = await aio_pika.connect_robust(
        host=os.environ.get('RABBITMQ_HOST'),
        port=5672,
    )

    queue_name = os.environ.get("RECEIVE_TRIP_DATA_QUEUE")
    send_gps_data_queue = os.environ.get("SEND_GPS_DATA_QUEUE")

    async with connection:
        channel = await connection.channel()

        await channel.set_qos(prefetch_count=10)

        queue = await channel.declare_queue(
            queue_name,
            durable=True,
            exclusive=False,
            auto_delete=False
        )

        sending_channel = await connection.channel()

        await channel.declare_queue(
            send_gps_data_queue,
            durable=True,
            exclusive=False,
            auto_delete=False
        )

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    loop = asyncio.get_running_loop()
                    loop.create_task(
                        consumer_handler(
                            message=json.loads(message.body),
                            sending_channel=sending_channel
                        )
                    )
                    if queue.name in message.body.decode():
                        break


if __name__ == "__main__":
    asyncio.run(main())
