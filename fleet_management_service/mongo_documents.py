from enum import Enum


# Define all kinds of documents here
# So that names of documents can be managed easily
class MongoDocumentsEnum(Enum):
    VEHICLES = "vehicles"
    DRIVERS = "drivers"
    TRIPS = "trips"
