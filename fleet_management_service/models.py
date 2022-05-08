from pydantic import BaseModel, Field
from bson import ObjectId
from typing import Optional


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class DriverModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    full_name: str = Field(...)
    points: int = Field(...)

    class Config:
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "full_name": "John Doe",
                "points": "10",
            }
        }


class UpdateDriverModel(BaseModel):
    full_name: Optional[str]
    points: Optional[int]

    class Config:
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "full_name": "John Doe",
                "points": "10",
            }
        }


class VehicleModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    type: str = Field(...)
    registration: str = Field(...)
    driver: Optional[DriverModel]

    class Config:
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "type": "Truck",
                "registration": "ABC-0-EFG",
            }
        }


class UpdateVehicleModel(BaseModel):
    type: Optional[str]
    registration: Optional[str]
    driver: Optional[DriverModel]

    class Config:
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "type": "Truck",
                "registration": "ABC-0-EFG",
            }
        }


class GeoPoint(BaseModel):
    lat: float = Field(...)
    long: float = Field(...)


class TripModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    depature_geo_point: GeoPoint
    destination_geo_point: GeoPoint
    vehicle: Optional[VehicleModel]
    trip_completed: Optional[bool]

    class Config:
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "depature_geo_point": {
                    "lat": 0,
                    "long": 0
                },
                "destination_geo_point": {
                    "lat": 0,
                    "long": 0
                },
                "trip_completed": False
            }
        }


class UpdateTripModel(BaseModel):
    depature_geo_point: Optional[GeoPoint]
    destination_geo_point: Optional[GeoPoint]

    class Config:
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "depature_geo_point": {
                    "lat": 0,
                    "long": 0
                },
                "destination_geo_point": {
                    "lat": 0,
                    "long": 0
                },
            }
        }
