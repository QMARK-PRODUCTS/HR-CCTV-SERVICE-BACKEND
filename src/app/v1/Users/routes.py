from fastapi import APIRouter
from src.app.v1.Users.api.controller import *

router = APIRouter()

routes = [
    {
        "route": "",
        "method": ["POST"],
        "handler": AddNewUser,
        "name": "Add new user"
    },
    {
        "route": "/admin",
        "method": ["POST"],
        "handler": CreateAdminUser,
        "name": "Create admin"
    },
    {
        "route": "/login",
        "method": ["POST"],
        "handler": AuthenticateUser,
        "name": "Login"
    },
    {
        "route": "",
        "method": ["PUT"],
        "handler": UpdateUser,
        "name": "Update user"
    },
    {
        "route": "",
        "method": ["GET"],
        "handler": GetUsers,
        "name": "Get users"
    },
    {
        "route": "/{userId}",
        "method": ["GET"],
        "handler": GetUserById,
        "name": "Get user"
    },
    {
        "route": "/{userId}",
        "method": ["DELETE"],
        "handler": DeleteUser,
        "name": "Delete user"
    },
    {
        "route": "/refresh",
        "method": ["POST"],
        "handler": RefreshAccessToken,
        "name": "Refresh Access Token"
    },
    {
        "route": "/validate",
        "method": ["POST"],
        "handler": ValidateAccessToken,
        "name": "Validate Access Token"
    }
]

for route in routes:
    router.add_api_route(route["route"], route["handler"], methods=route["method"], name=route["name"])