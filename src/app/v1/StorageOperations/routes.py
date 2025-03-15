from fastapi import APIRouter
from src.app.v1.StorageOperations.api.controller import *

router = APIRouter()

routes = [
    {
        "route": "/uploads/{user_id}/{image_name}",
        "method": ["GET"],
        "handler": GetUserImage,
        "name": "Get User Image"
    },
    {
        "route": "/function-recordings/{function_id}",
        "method": ["GET"],
        "handler": GetFunctionVideoStream,
        "name": "Get Function Recording"
    }
]

for route in routes:
    router.add_api_route(path=route["route"], endpoint=route["handler"], methods=route["method"], name=route["name"])
    
    
