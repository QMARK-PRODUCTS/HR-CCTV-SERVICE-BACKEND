from fastapi import APIRouter
from src.app.v1.DetectFaces.api.controller import *
from src.app.v1.DetectFaces.Services.trainFaces import *
router = APIRouter()

webSocketRoutes = [
    {
        "route": "/stream",
        "method": ["WEBSOCKET"],
        "handler": DetectFacesWebsocket,
        "name": "WebSocket Face Detection"
    }
]

restRoutes = [
    {
        "route": "/train",
        "method": ["POST"],
        "handler": TrainFaces,
        "name": "Train Faces"
    }
]

for route in restRoutes:
    router.add_api_route(route["route"], route["handler"], methods=route["method"], name=route["name"])
    
for route in webSocketRoutes:
    router.add_websocket_route(route["route"], route["handler"], name=route["name"])