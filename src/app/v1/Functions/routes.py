from fastapi import APIRouter
from src.app.v1.Functions.api.controller import *

router = APIRouter()

routes = [
    {
        "route": "",
        "method": ["POST"],
        "handler": AddNewFunction,
        "name": "Add new function"
    },
    {
        "route": "",
        "method": ["GET"],
        "handler": GetFunctions,
        "name": "Get functions"
    },
    {
        "route": "",
        "method": ["DELETE"],
        "handler": DeleteFunction,
        "name": "Delete function"
    },
    {
        "route": "",
        "method": ["PUT"],
        "handler": UpdateFunction,
        "name": "Update function"
    },
    {
        "route": "/recordings/{functionId}",
        "method": ["GET"],
        "handler": GetFunctionRecordings,
        "name": "Get function recordings"
    }
]

for route in routes:
    router.add_api_route(route["route"], route["handler"], methods=route["method"], name=route["name"])