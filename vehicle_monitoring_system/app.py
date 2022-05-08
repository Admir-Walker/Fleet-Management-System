import os
import json
import asyncio
import aio_pika
import enum
import motor.motor_asyncio
from dotenv import load_dotenv
from math import cos, asin, sqrt, pi

load_dotenv()
SEND_POINTS_QUEUE = os.environ.get('SEND_POINTS_QUEUE')

# db
client = motor.motor_asyncio.AsyncIOMotorClient(os.environ.get("MONGODB_URL"))
db = client.vehicle_monitoring_system


class MongoDocumentsEnum(enum.Enum):
    GPS_DATA = "gps_data"


async def publish(channel, body, queue_name):
    await channel.default_exchange.publish(
        aio_pika.Message(
            body=json.dumps(body).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        ),
        routing_key=queue_name
    )


async def save_gps_data(gps_data):

    if (gps_data_db := await db[MongoDocumentsEnum.GPS_DATA.value].find_one({"trip_id": gps_data.get("trip_id", None)})) is not None:
        gps_data_db["trip_data"].append(
            {
                "current_geo_point": gps_data.get("current_geo_point"),
                "speed": gps_data.get("speed"),
                "timestamp": gps_data.get("timestamp")
            }
        )
        await db[MongoDocumentsEnum.GPS_DATA.value].update_one({"_id": gps_data_db["_id"]}, {"$set": gps_data_db})

    else:
        trip_data = {
            "current_geo_point": gps_data.pop("current_geo_point"),
            "speed": gps_data.pop("speed"),
            "timestamp": gps_data.pop("timestamp")
        }
        gps_data["trip_data"] = [trip_data]
        await db[MongoDocumentsEnum.GPS_DATA.value].insert_one(gps_data)


# Optimized formula for calculating distance between two geo points
# https://stackoverflow.com/questions/27928/calculate-distance-between-two-latitude-longitude-points-haversine-formula
def distance(lat1, lon1, lat2, lon2):
    p = pi/180
    a = 0.5 - cos((lat2-lat1)*p)/2 + cos(lat1*p) * \
        cos(lat2*p) * (1-cos((lon2-lon1)*p))/2
    return abs(12742 * asin(sqrt(a)))


async def calculate_points_from_gps_data(gps_data):
    final_gps_data = await db[MongoDocumentsEnum.GPS_DATA.value].find_one({"trip_id": gps_data.get("trip_id", None)})

    speed_boundaries_kilometeres = {
        "60-80": 0.0,  # 1 point per km
        "80-100": 0.0,  # 2 points per km
        "100+": 0.0  # 5 points per km
    }

    for i in range(0, len(final_gps_data["trip_data"])-1):
        starting_speed_interval = final_gps_data["trip_data"][i]["speed"]
        ending_speed_interval = final_gps_data["trip_data"][i+1]["speed"]

        avg_speed = int((starting_speed_interval+ending_speed_interval) / 2)

        if avg_speed < 60:
            continue

        key = ""
        if avg_speed >= 60 and avg_speed < 80:
            key = "60-80"
        elif avg_speed >= 80 and avg_speed < 100:
            key = "80-100"
        else:
            key = "100+"

        speed_boundaries_kilometeres[key] += distance(
            final_gps_data["trip_data"][i]["current_geo_point"]["lat"],
            final_gps_data["trip_data"][i]["current_geo_point"]["long"],
            final_gps_data["trip_data"][i+1]["current_geo_point"]["lat"],
            final_gps_data["trip_data"][i+1]["current_geo_point"]["long"]
        )

    return int(speed_boundaries_kilometeres["60-80"]) + \
        int(speed_boundaries_kilometeres["80-100"])*2 + \
        int(speed_boundaries_kilometeres["100+"])*5


async def consumer_handler(message, sending_channel):
    await save_gps_data(message)

    if message.get("trip_finished", False):
        points = await calculate_points_from_gps_data(message)
        body = {
            "points": points,
            "trip_id": message.get("trip_id"),
            "driver_id": message.get("driver_id")

        }
        await publish(sending_channel, body, os.environ.get('SEND_POINTS_QUEUE'))


async def main() -> None:
    # logging.basicConfig(level=logging.DEBUG)
    connection = await aio_pika.connect_robust(
        host=os.environ.get('RABBITMQ_HOST'),
        port=5672,
    )

    queue_name = os.environ.get("RECEIVE_GPS_DATA_QUEUE")
    send_points_queue = os.environ.get("SEND_POINTS_QUEUE")

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
            send_points_queue,
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
