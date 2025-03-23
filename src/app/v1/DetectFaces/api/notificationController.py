from fastapi import WebSocket, WebSocketDisconnect, BackgroundTasks
import pika
import threading
import asyncio
import json


# RabbitMQ connection parameters
RABBITMQ_HOST = "localhost"
QUEUE_NAME = "notificationsAlerts"

# Initialize RabbitMQ connection
def get_rabbitmq_connection():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    return connection


async def sendMessageToQueue(data: dict):
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)
    
    # Publish message
    channel.basic_publish(exchange="", routing_key=QUEUE_NAME, body=json.dumps(data))
    connection.close()
    
    return {"message": "Sent successfully"}

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()


async def notificationWebsocket(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await asyncio.sleep(1)  # Keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Consume messages from RabbitMQ and send via WebSocket
def consume_messages():
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)

    def callback(ch, method, properties, body):
        message = body.decode()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(manager.send_message(message))

    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

# Run RabbitMQ consumer in a background thread
threading.Thread(target=consume_messages, daemon=True).start()