from fastapi import WebSocket, WebSocketDisconnect, BackgroundTasks
import pika
import threading
import asyncio
import json
from .notifier import Notifier

# RabbitMQ connection parameters
RABBITMQ_HOST = "localhost"
QUEUE_NAME = "notificationsAlerts"

notifier = Notifier()

# Initialize RabbitMQ connection
def get_rabbitmq_connection():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, port=5672))
    return connection


async def sendMessageToQueue(message: str):
    if not notifier.is_ready:
        await notifier.setup("test")
    await notifier.push(
        {
            "timestamp": 259816,
            "people_count": 1,
            "message": f'{message}'
        }
    )

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: set[WebSocket] = set()
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        print(f"✅ WebSocket connected! Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: str):
        for connection in self.active_connections:
            try:
                print(f"📤 Sending to WebSocket: {message}")
                await connection.send_text(message)
            except Exception as e:
                print(f"⚠️ WebSocket error: {e}")
                self.disconnect(connection)

manager = ConnectionManager()


async def notificationWebsocket(websocket: WebSocket):
    await notifier.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        notifier.remove(websocket)

# # Consume messages from RabbitMQ and send via WebSocket
# def consume_messages():
#     connection = get_rabbitmq_connection()
#     channel = connection.channel()
#     channel.queue_declare(queue=QUEUE_NAME)

#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)  # Ensure a dedicated event loop

#     def callback(ch, method, properties, body):
#         message = body.decode()
#         print(f"📩 Received from RabbitMQ: {message}")  # Debug
#         loop.call_soon_threadsafe(asyncio.create_task, manager.send_message(message))

#     channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=True)
#     print("🔄 Listening for messages...")
#     channel.start_consuming()

# threading.Thread(target=consume_messages, daemon=True).start()