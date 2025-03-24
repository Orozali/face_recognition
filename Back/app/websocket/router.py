from fastapi import WebSocket, APIRouter, Depends, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.service.insightface import process_frame
from app.core.database import get_db
from app.websocket.manager import ws_manager
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

ws_router = APIRouter()


@ws_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    await ws_manager.connect(websocket)    
    try:
        while True:
            data = await websocket.receive_bytes()
    
            result = await process_frame(data, db)
            await websocket.send_json(result)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        print("Client disconnected.")
    except Exception as e:
        print(f"🚨 WebSocket Error: {e}")
        await websocket.send_json({"error": str(e)})
