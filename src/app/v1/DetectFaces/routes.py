from fastapi import APIRouter
from src.app.v1.DetectFaces.api.controller import *

router = APIRouter()

routes = [
    {
        "route": "/stream",
        "method": ["WEBSOCKET"],
        "handler": DetectFacesWebsocket,
        "name": "WebSocket Face Detection"
    }
]

for route in routes:
    router.add_websocket_route(route["route"], route["handler"], name=route["name"])