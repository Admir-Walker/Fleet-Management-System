from dependencies import db
from pika_client import pika_client
from mongo_documents import MongoDocumentsEnum
from fastapi import APIRouter, Body, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import List
from models import TripModel, UpdateTripModel


router = APIRouter(
    prefix="/api/trips",
    tags=["trips"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_description="Get all trips", response_model=List[TripModel])
async def get_all_trips():
    trips = []

    for result in await db[MongoDocumentsEnum.TRIPS.value].find().to_list(length=100):
        trips.append(result)

    return trips


@router.post("/", response_description="Add new trip", response_model=TripModel)
async def create_trip(trip: TripModel = Body(...)):
    trip = jsonable_encoder(trip)
    new_trip = await db[MongoDocumentsEnum.TRIPS.value].insert_one(trip)
    created_trip = await db[MongoDocumentsEnum.TRIPS.value].find_one({"_id": new_trip.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_trip)


@router.get(
    "/{id}", response_description="Get a single trip", response_model=TripModel
)
async def show_trip(id: str):
    if (trip := await db[MongoDocumentsEnum.TRIPS.value].find_one({"_id": id})) is not None:
        return trip

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Trip {id} not found"
    )


@router.put("/{id}", response_description="Update a trip", response_model=UpdateTripModel)
async def update_trip(id: str, trip: UpdateTripModel = Body(...)):
    trip = {k: v for k, v in trip.dict().items() if v is not None}

    if len(trip) >= 1:
        update_result = await db[MongoDocumentsEnum.TRIPS.value].update_one({"_id": id}, {"$set": trip})

        if update_result.modified_count == 1:
            if (
                updated_trip := await db[MongoDocumentsEnum.TRIPS.value].find_one({"_id": id})
            ) is not None:
                return updated_trip

    if (existing_trip := await db[MongoDocumentsEnum.TRIPS.value].find_one({"_id": id})) is not None:
        return existing_trip

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Trip {id} not found"
    )


@router.delete("/{id}", response_description="Delete a trip")
async def delete_trip(id: str):
    delete_result = await db[MongoDocumentsEnum.TRIPS.value].delete_one({"_id": id})

    if delete_result.deleted_count == 1:
        return JSONResponse(status_code=status.HTTP_200_OK)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Trip {id} not found"
    )


@router.put(
    "/{trip_id}/assign_vehicle/{vehicle_id}",
    response_description="Assign vehicle to a trip",
    response_model=TripModel
)
async def assign_vehicle_to_a_trip(trip_id: str, vehicle_id: str):
    trip = await db[MongoDocumentsEnum.TRIPS.value].find_one({"_id": trip_id})
    if trip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trip {trip_id} not found"
        )

    if trip["trip_completed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Trip is already completed"
        )

    vehicle = await db[MongoDocumentsEnum.VEHICLES.value].find_one({"_id": vehicle_id})
    if vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle {vehicle_id} not found"
        )

    trip["vehicle_id"] = vehicle.get("_id")

    await db[MongoDocumentsEnum.TRIPS.value].update_one({"_id": trip_id}, {"$set": trip})

    driver_id = vehicle.get("driver_id", None)

    if driver_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vehicle doesn't have assigned any drivers"
        )

    # TODO update values
    pika_client.send_message({
        "vehicle_id": vehicle_id,
        "trip_id": trip_id,
        "driver_id": driver_id,
        "depature_geo_point": trip["depature_geo_point"],
        "destination_geo_point": trip["destination_geo_point"]
    })

    trip["vehicle"] = vehicle

    return trip
