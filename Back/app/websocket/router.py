from typing import Optional
from fastapi import WebSocket, APIRouter, Depends, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.service.insightface import process_frame
from app.service.recognition import capture_faces
from app.core.database import get_db
from app.websocket.manager import ws_manager
import logging
import numpy as np
import cv2

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

ws_router = APIRouter()

latest_frame: Optional[np.ndarray] = None
@ws_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    await ws_manager.connect(websocket)    
    try:
        while True:
            data = await websocket.receive_bytes()
            global latest_frame
            latest_frame = np.frombuffer(data, np.uint8)
            latest_frame = cv2.imdecode(latest_frame, cv2.IMREAD_COLOR)

            result = await capture_faces(data, db)
            await websocket.send_json(result)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        print("Client disconnected.")
    except Exception as e:
        print(f"🚨 WebSocket Error: {e}")
        await websocket.send_json({"error": str(e)})
