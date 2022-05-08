from dependencies import db
from mongo_documents import MongoDocumentsEnum
from fastapi import APIRouter, Body, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import List
from models import UpdateVehicleModel, VehicleModel


router = APIRouter(
    prefix="/api/vehicles",
    tags=["vehicles"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_description="Get all vehicles", response_model=List[VehicleModel])
async def get_all_vehicles():
    vehicles = []

    for result in await db[MongoDocumentsEnum.VEHICLES.value].find().to_list(length=100):
        vehicles.append(result)

    return vehicles


@router.post("/", response_description="Add new vehicle", response_model=VehicleModel)
async def create_vehicle(vehicle: VehicleModel = Body(...)):
    vehicle = jsonable_encoder(vehicle)
    new_vehicle = await db[MongoDocumentsEnum.VEHICLES.value].insert_one(vehicle)
    created_vehicle = await db[MongoDocumentsEnum.VEHICLES.value].find_one({"_id": new_vehicle.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_vehicle)


@router.get(
    "/{id}", response_description="Get a single vehicle", response_model=VehicleModel
)
async def show_vehicle(id: str):
    if (vehicle := await db[MongoDocumentsEnum.VEHICLES.value].find_one({"_id": id})) is not None:
        return vehicle

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Vehicle {id} not found"
    )


@router.put("/{id}", response_description="Update a vehicle", response_model=UpdateVehicleModel)
async def update_vehicle(id: str, vehicle: UpdateVehicleModel = Body(...)):
    vehicle = {k: v for k, v in vehicle.dict().items() if v is not None}

    if len(vehicle) >= 1:
        update_result = await db[MongoDocumentsEnum.VEHICLES.value].update_one({"_id": id}, {"$set": vehicle})

        if update_result.modified_count == 1:
            if (
                updated_vehicle := await db[MongoDocumentsEnum.VEHICLES.value].find_one({"_id": id})
            ) is not None:
                return updated_vehicle

    if (existing_vehicle := await db[MongoDocumentsEnum.VEHICLES.value].find_one({"_id": id})) is not None:
        return existing_vehicle

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Vehicle {id} not found"
    )


@router.delete("/{id}", response_description="Delete a vehicle")
async def delete_vehicle(id: str):
    delete_result = await db[MongoDocumentsEnum.VEHICLES.value].delete_one({"_id": id})

    if delete_result.deleted_count == 1:
        return JSONResponse(status_code=status.HTTP_200_OK)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Vehicle {id} not found"
    )


@router.put(
    "/{vehicle_id}/assign_driver/{driver_id}",
    response_description="Assign driver to a vehicle",
    response_model=VehicleModel
)
async def assign_driver_to_a_vehicle(vehicle_id: str, driver_id: str):
    vehicle = await db[MongoDocumentsEnum.VEHICLES.value].find_one({"_id": vehicle_id})
    if vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle {vehicle_id} not found"
        )

    driver_assigned = await db[MongoDocumentsEnum.VEHICLES.value].find_one({"driver_id": driver_id})

    if driver_assigned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Driver {driver_id} already assigned a vehicle"
        )

    driver = await db[MongoDocumentsEnum.DRIVERS.value].find_one({"_id": driver_id})
    if driver is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver {driver_id} not found"
        )

    vehicle["driver_id"] = driver.get("_id")

    await db[MongoDocumentsEnum.VEHICLES.value].update_one({"_id": vehicle_id}, {"$set": vehicle})

    vehicle["driver"] = driver

    return vehicle
