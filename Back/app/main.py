from fastapi import FastAPI

from app.cron.scheduler import scheduler
from contextlib import asynccontextmanager
from app.websocket.router import ws_router
from app.service.recognition import capture_faces

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting scheduler...")
    if not scheduler.running:
        scheduler.start()
    yield
    print("Shutting down scheduler...")
    scheduler.shutdown()

app = FastAPI(title="FastAPI PostgreSQL Example", lifespan=lifespan)
app.include_router(ws_router)

@app.get("/time")
async def time():
    return await capture_faces("08:55")
