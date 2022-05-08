from dependencies import db
from mongo_documents import MongoDocumentsEnum


async def consume_point_messages(message):
    driver = await db[MongoDocumentsEnum.DRIVERS.value].find_one({"_id": message["driver_id"]})

    driver["points"] += message["points"]

    await db[MongoDocumentsEnum.DRIVERS.value].update_one({"_id": message["driver_id"]}, {"$set": driver})

    trip = await db[MongoDocumentsEnum.TRIPS.value].find_one({"_id": message["trip_id"]})

    trip["trip_completed"] = True

    await db[MongoDocumentsEnum.TRIPS.value].update_one({"_id": message["trip_id"]}, {"$set": trip})
