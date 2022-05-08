import asyncio
from fastapi import FastAPI
from routers import vehicles, drivers, trips
from pika_client import pika_client

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    # Background task to consume incoming messages
    from consumers import consume_point_messages
    loop = asyncio.get_running_loop()
    await loop.create_task(pika_client.consume(loop, consume_point_messages))

app.include_router(vehicles.router)
app.include_router(drivers.router)
app.include_router(trips.router)
