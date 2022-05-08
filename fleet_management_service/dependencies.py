import os
import motor.motor_asyncio

from dotenv import load_dotenv

load_dotenv()

# db
client = motor.motor_asyncio.AsyncIOMotorClient(os.environ.get("MONGODB_URL"))
db = client.fleet_management_service
