from fastapi import APIRouter
from src.app.v1.Users.api.controller import *

router = APIRouter()

routes = [
    {
        "route": "/model",
        "method": ["POST"],
        "handler": AddNewUserModel,
        "name": "Add new user model"
    },
    {
        "route": "/model",
        "method": ["GET"],
        "handler": GetUserModels,
        "name": "Get user models"
    },
    {
        "route": "/model/{userModelId}",
        "method": ["DELETE"],
        "handler": DeleteUserModel,
        "name": "Delete user model"
    },
    {
        "route": "",
        "method": ["POST"],
        "handler": AddNewUser,
        "name": "Add new user"
    },
    {
        "route": "",
        "method": ["GET"],
        "handler": GetUsers,
        "name": "Get users"
    },
    {
        "route": "/{userId}",
        "method": ["DELETE"],
        "handler": DeleteUser,
        "name": "Delete user"
    }
]

for route in routes:
    router.add_api_route(route["route"], route["handler"], methods=route["method"], name=route["name"])