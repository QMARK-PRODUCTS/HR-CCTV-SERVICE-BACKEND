from dotenv import load_dotenv
import os
from fastapi import HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from src.app.v1.StorageOperations.models.models import *
from src.database.db import get_session
from sqlmodel import Session, select
from typing import Annotated
from fastapi import Depends
import cv2

SessionDep = Annotated[Session, Depends(get_session)]

load_dotenv()

STORAGE_DIR = os.getenv("STORAGE_DIR", "./storage")  # Default to "./storage" if not set

async def GetUserImage(user_id: str, image_name: str):
    """Serve images from the server"""
    image_path = os.path.join(STORAGE_DIR, "users", user_id ,image_name)

    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(image_path)


async def GetFunctionVideoStream(function_id: str, session: SessionDep):
    function = session.query(FunctionRecordings).filter(FunctionRecordings.id == function_id).first()
    if not function:
        raise HTTPException(status_code=404, detail="Function not found")

    file_path = function.recording
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video not found")

    cap = cv2.VideoCapture(file_path)
    
    def generate():
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")
    
    
    
    