from typing import List
from starlette.websockets import WebSocket

import asyncio, json
from aio_pika import connect, Message, IncomingMessage


class Notifier:
    def __init__(self):
        self.connections: List[WebSocket] = []
        self.is_ready = False

    async def setup(self, queue_name: str):
        self.rmq_conn = await connect(
            "amqp://guest:guest@localhost/",
            loop=asyncio.get_running_loop()
        )
        self.channel = await self.rmq_conn.channel()
        self.queue_name = queue_name
        queue = await self.channel.declare_queue(self.queue_name)
        await queue.consume(self._notify, no_ack=True)
        self.is_ready = True

    async def push(self, msg: dict):
        json_msg = json.dumps(msg)  # Convert dict to JSON string
        await self.channel.default_exchange.publish(
            Message(json_msg.encode("utf-8")),  # Encode the JSON string
            routing_key=self.queue_name,
        )
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)

    def remove(self, websocket: WebSocket):
        self.connections.remove(websocket)

    async def _notify(self, message: IncomingMessage):
        living_connections = []
        
        # Decode and convert message body from bytes -> string -> dictionary
        decoded_message = message.body.decode("utf-8")  
        parsed_message = json.loads(decoded_message)  # Convert string to dict
        
        for websocket in self.connections:
            try:
                # Convert dict to string before sending
                await websocket.send_text(json.dumps(parsed_message))
                living_connections.append(websocket)  # Keep connection alive
            except Exception as e:
                print(f"⚠️ WebSocket Error: {e}")

        self.connections = living_connections
