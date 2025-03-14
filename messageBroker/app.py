import pika
import asyncio
import json
import websockets
import threading

rabbitmq_host = "localhost"  # Ensure RabbitMQ is accessible
websocket_clients = set()

async def notify_clients(message):
    """Send message to all connected WebSocket clients."""
    disconnected_clients = set()
    for client in websocket_clients:
        try:
            await client.send(message)
        except:
            disconnected_clients.add(client)  # Mark disconnected clients

    for client in disconnected_clients:
        websocket_clients.remove(client)  # Remove disconnected clients

async def websocket_server(websocket, path):  # Fix: Accept `path` argument
    """WebSocket server to maintain connections."""
    websocket_clients.add(websocket)
    try:
        async for _ in websocket:
            pass  # Keep connection open
    except:
        pass  # Ignore errors
    finally:
        websocket_clients.remove(websocket)  # Ensure removal on disconnect

def rabbitmq_listener(loop):
    """Listen for messages from RabbitMQ and notify WebSocket clients."""
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
    channel = connection.channel()
    channel.queue_declare(queue="face_notifications")

    def callback(ch, method, properties, body):
        message = body.decode("utf-8")
        loop.call_soon_threadsafe(asyncio.create_task, notify_clients(message))

    channel.basic_consume(queue="face_notifications", on_message_callback=callback, auto_ack=True)
    print("Listening for face detection notifications...")
    channel.start_consuming()

async def main():
    """Start WebSocket server."""
    async with websockets.serve(websocket_server, "0.0.0.0", 6789):  # WebSocket Fix
        await asyncio.Future()  # Keep the server running

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Start RabbitMQ listener in a separate thread
    rabbitmq_thread = threading.Thread(target=rabbitmq_listener, args=(loop,), daemon=True)
    rabbitmq_thread.start()

    # Run WebSocket server in the main thread
    loop.run_until_complete(main())