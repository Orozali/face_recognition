from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.cron_active = False
        self.lesson_time = "08:00"

    def set_cron_active(self, active: bool):
        self.cron_active = active

    def set_lesson_time(self, lesson_time: str):
        self.lesson_time = lesson_time


    def add_connection(self, lesson_time: str, websocket: WebSocket):
        self.active_connections[lesson_time] = websocket
    def remove_connection(self, lesson_time: str):
        del self.active_connections[lesson_time]

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Error sending message: {e}")

ws_manager = ConnectionManager()
