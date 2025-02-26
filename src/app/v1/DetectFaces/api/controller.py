import os
import cv2
import torch
import numpy as np
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from ultralytics import YOLO
from typing import List

face_detector = YOLO("yolov8n-face.pt")  # Assuming YOLO face model

class FaceCounter:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

face_counter = FaceCounter()

async def DetectFacesWebsocket(websocket: WebSocket):
    # Get the `source` query parameter (default to webcam "0" if not provided)
    source = websocket.query_params.get("source", "0")

    # Open webcam or RTSP stream
    cap = cv2.VideoCapture(0 if source == "0" else source)

    if not cap.isOpened():
        await websocket.send_json({"error": "Unable to open video source."})
        await websocket.close()
        return

    await face_counter.connect(websocket)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                await websocket.send_json({"error": "Failed to retrieve frame."})
                break  # Stop loop if frame retrieval fails
            
            faces = extract_faces(frame)
            face_count = len(faces)

            # Send face count update
            await face_counter.broadcast({"face_count": face_count})

            await asyncio.sleep(0.1)  # Avoid overloading

    except WebSocketDisconnect:
        print("Client disconnected.")
    finally:
        face_counter.disconnect(websocket)
        cap.release()  # Release video capture


def extract_faces(img):
    """Detect faces and return cropped face images."""
    faces = []
    results = face_detector(img)
    
    for result in results:
        boxes = result.boxes.xyxy.cpu().numpy()
        for box in boxes:
            x1, y1, x2, y2 = map(int, box)
            face = img[y1:y2, x1:x2]
            face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
            face = cv2.resize(face, (160, 160))
            faces.append(face)
    
    return faces
