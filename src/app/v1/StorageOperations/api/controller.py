from dotenv import load_dotenv
import os
from fastapi import HTTPException
from fastapi.responses import FileResponse

load_dotenv()

STORAGE_DIR = os.getenv("STORAGE_DIR", "./storage")  # Default to "./storage" if not set

async def GetUserImage(user_id: str, image_name: str):
    """Serve images from the server"""
    image_path = os.path.join(STORAGE_DIR, "users", user_id ,image_name)

    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(image_path)