from dependencies import db
from mongo_documents import MongoDocumentsEnum
from fastapi import APIRouter, Body, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import List
from models import DriverModel, UpdateDriverModel


router = APIRouter(
    prefix="/api/drivers",
    tags=["drivers"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_description="Get all drivers", response_model=List[DriverModel])
async def get_all_drivers():
    drivers = []

    for result in await db[MongoDocumentsEnum.DRIVERS.value].find().to_list(length=100):
        drivers.append(result)

    return drivers


@router.post("/", response_description="Add new driver", response_model=DriverModel)
async def create_driver(driver: DriverModel = Body(...)):
    driver = jsonable_encoder(driver)
    new_driver = await db[MongoDocumentsEnum.DRIVERS.value].insert_one(driver)
    created_driver = await db[MongoDocumentsEnum.DRIVERS.value].find_one({"_id": new_driver.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_driver)


@router.get(
    "/{id}", response_description="Get a single driver", response_model=DriverModel
)
async def show_driver(id: str):
    if (driver := await db[MongoDocumentsEnum.DRIVERS.value].find_one({"_id": id})) is not None:
        return driver

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Driver {id} not found"
    )


@router.put("/{id}", response_description="Update a driver", response_model=UpdateDriverModel)
async def update_driver(id: str, driver: UpdateDriverModel = Body(...)):
    driver = {k: v for k, v in driver.dict().items() if v is not None}

    if len(driver) >= 1:
        update_result = await db[MongoDocumentsEnum.DRIVERS.value].update_one({"_id": id}, {"$set": driver})

        if update_result.modified_count == 1:
            if (
                updated_driver := await db[MongoDocumentsEnum.DRIVERS.value].find_one({"_id": id})
            ) is not None:
                return updated_driver

    if (existing_driver := await db[MongoDocumentsEnum.DRIVERS.value].find_one({"_id": id})) is not None:
        return existing_driver

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Driver {id} not found"
    )


@router.delete("/{id}", response_description="Delete a driver")
async def delete_driver(id: str):
    delete_result = await db[MongoDocumentsEnum.DRIVERS.value].delete_one({"_id": id})

    if delete_result.deleted_count == 1:
        return JSONResponse(status_code=status.HTTP_200_OK)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Driver {id} not found"
    )
