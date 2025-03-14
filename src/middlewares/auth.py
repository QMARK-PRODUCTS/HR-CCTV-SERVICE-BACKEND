from fastapi import Request
from fastapi.responses import JSONResponse
from src.app.v1.Users.services.auth import *
async def ValidateAccessToken(request: Request, call_next):
    # Exclude authentication for specific routes if needed
    public_routes = ["/docs", "/openapi.json", "/api/v1/auth/login"]  # Example: Login route
    if request.url.path in public_routes:
        return await call_next(request)
    
    # Extract token from headers
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"detail": "Unauthorized: Missing or invalid token"})
    
    token = auth_header.split(" ")[1]  # Extract the token
    if not verify_token(token):
        return JSONResponse(status_code=401, content={"detail": "Unauthorized: Invalid token"})

    return await call_next(request)


async def GetNewAccessToken(request: Request, call_next):
    # Extract refresh token from headers
    refresh_token = request.headers.get("Refresh-Token")
    if not refresh_token:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized: Missing refresh token"})
    
    new_token = generate_new_token(refresh_token)
    if not new_token:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized: Invalid refresh token"})

    return JSONResponse(status_code=200, content={"accessToken": new_token})