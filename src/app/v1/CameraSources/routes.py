from fastapi import APIRouter
from src.app.v1.CameraSources.api.controller import *
from src.app.v1.CameraSources.services.ConvertRTSP import *
router = APIRouter()

routes = [
    {
        "route": "",
        "method": ["POST"],
        "handler": AddNewConnection,
        "name": "Add new camera connection"
    },
    {
        "route": "",
        "method": ["GET"],
        "handler": GetCameraSources,
        "name": "Get camera sources"
    },
    {
        "route": "/{camera_id}",
        "method": ["PUT"],
        "handler": UpdateCameraSource,
        "name": "Update camera sources"
    },
    {
        "route": "/{camera_id}",
        "method": ["DELETE"],
        "handler": DeleteCameraSource,
        "name": "Delete camera sources"
    },
    # {
    #     "route": "/convert/",
    #     "method": ["POST"],
    #     "handler": convert_rtsp_to_hls,
    #     "name": "Convert RTSP to HLS"
    # }
]

for route in routes:
    router.add_api_route(route["route"], route["handler"], methods=route["method"], name=route["name"])