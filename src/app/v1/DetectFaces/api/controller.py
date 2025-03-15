import os
import cv2
import numpy as np
import asyncio
import pickle
import torch
import pika, json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List
from scipy.spatial.distance import cosine
from ultralytics import YOLO
from facenet_pytorch import InceptionResnetV1
from collections import deque, Counter
from src.app.v1.Functions.models.models import FunctionInfo
import mediapipe as mp
from datetime import datetime
from src.database.db import get_session

VOTE_WINDOW = 10
FRAME_SKIP = 3
MODELS_DIR = f"{os.getenv('STORAGE_DIR', './storage')}/models/"
SessionLocal = get_session()

face_detector = YOLO("yolov8n-face.pt")
resnet = InceptionResnetV1(pretrained='vggface2').eval()
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=10, min_detection_confidence=0.5)

face_vote_memory = {}


# RabbitMQ Connection
rabbitmq_host = os.getenv("RABBITMQ_HOST", "localhost")

rabbitmq_connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
rabbitmq_channel = rabbitmq_connection.channel()
rabbitmq_channel.queue_declare(queue="face_notifications")

def load_face_embeddings():
    with open(MODELS_DIR + 'allFaces.pkl', 'rb') as f:
        return pickle.load(f)

def encode(img):
    img = torch.Tensor(img).unsqueeze(0)
    if img.shape[1] != 3:
        img = img.permute(0, 3, 1, 2)
    return resnet(img)

def align_face(image, landmarks, image_width, image_height):
    left_eye = landmarks[159]
    right_eye = landmarks[386]
    left_eye_x, left_eye_y = int(left_eye.x * image_width), int(left_eye.y * image_height)
    right_eye_x, right_eye_y = int(right_eye.x * image_width), int(right_eye.y * image_height)
    
    dY, dX = right_eye_y - left_eye_y, right_eye_x - left_eye_x
    angle = np.degrees(np.arctan2(dY, dX)) - 180
    
    center = (image.shape[1] // 2, image.shape[0] // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(image, M, (image.shape[1], image.shape[0]), flags=cv2.INTER_CUBIC)

class FaceRecognition:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.all_people_faces = load_face_embeddings()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

face_recognition = FaceRecognition()

async def DetectFacesWebsocket(websocket: WebSocket):
    source = websocket.query_params.get("source", "0")
    # cap = cv2.VideoCapture(f'{os.getenv("STREAMING_SERVER")}api/v1/camera-sources/webcam-video')
    if source == "0":
        source = f'{os.getenv("STREAMING_SERVER")}api/v1/camera-sources/webcam-video'
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        await websocket.send_json({"error": "Unable to open video source."})
        await websocket.close()
        return

    await face_recognition.connect(websocket)
    frame_count = 0
    stable_identities = {}
    people_detected_start = None  # Timestamp for tracking

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                await websocket.send_json({"error": "Failed to retrieve frame."})
                break

            frame_count += 1
            if frame_count % FRAME_SKIP != 0:
                continue

            detected_faces = []
            results = face_detector(frame)

            for result in results:
                boxes = result.boxes.xyxy.cpu().numpy()
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box)
                    face = frame[y1:y2, x1:x2]

                    rgb_face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
                    results_mesh = face_mesh.process(rgb_face)
                    if results_mesh.multi_face_landmarks:
                        landmarks = results_mesh.multi_face_landmarks[0].landmark
                        face = align_face(face, landmarks, face.shape[1], face.shape[0])

                    face = cv2.resize(face, (160, 160))
                    face = np.transpose(face, (2, 0, 1))
                    face = (face / 255.0 - 0.5) / 0.5

                    img_embedding = encode(face).detach().numpy().flatten()
                    detect_dict = {k: min([cosine(v, img_embedding) for v in data["embeddings"]])
                                   for k, data in face_recognition.all_people_faces.items() if data["embeddings"]}

                    if not detect_dict or min(detect_dict.values()) >= 0.5:
                        min_key, image_url, value = "Undetected", "N/A", "0.00"
                    else:
                        min_key = min(detect_dict, key=detect_dict.get)
                        image_url = face_recognition.all_people_faces[min_key]["image_url"]
                        value = face_recognition.all_people_faces[min_key].get("value", "0.00")

                    face_id = (x1, y1, x2, y2)
                    if face_id not in stable_identities:
                        stable_identities[face_id] = {"label": min_key, "count": 0}

                    if stable_identities[face_id]["label"] == min_key:
                        stable_identities[face_id]["count"] += 1
                    else:
                        stable_identities[face_id] = {"label": min_key, "count": 0}

                    if stable_identities[face_id]["count"] >= 35:
                        stable_identities[face_id]["label"] = min_key

                    final_label = stable_identities[face_id]["label"]
                    detected_faces.append({"name": final_label, "image_url": image_url, "value": value})

            await websocket.send_json({"detected_faces": detected_faces})
            
            # Count number of people detected
            people_count = len(detected_faces)

            if people_count >= 1:
                loop = asyncio.get_running_loop()  # Get the event loop

                if people_detected_start is None:
                    people_detected_start = loop.time()  # Initialize start time

                elapsed_time = loop.time() - people_detected_start  # Calculate elapsed time

                if elapsed_time >= 5:
                    message = json.dumps({"timestamp": int(loop.time()), "people_count": people_count})
                    
                    try:
                        rabbitmq_channel.basic_publish(exchange="", routing_key="face_notifications", body=message)
                        print("Sent message to RabbitMQ:", message)  # Debugging output
                    except Exception as e:
                        print("RabbitMQ Error:", str(e))  # Catch RabbitMQ errors

                    people_detected_start = None  # Reset timer after sending

            else:
                people_detected_start = None  # Reset if no people are detected

            await asyncio.sleep(0.3)

    except WebSocketDisconnect:
        print("Client disconnected.")
    finally:
        face_recognition.disconnect(websocket)
        cap.release()


async def DetectFacesBackground(func, session):
    """Detect faces from a camera source and handle recording + notification"""
    source = func.camerasAssigned.get("cameras", "0")
    if source == "0" or source == []:
        source = f'{os.getenv("STREAMING_SERVER")}api/v1/camera-sources/webcam-video'

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"Error: Unable to open video source for function {func.name}")
        return

    frame_count = 0
    people_detected_start = None
    recording_start_time = None
    recording = False
    out = None
    people_count_log = []
    file_path = None

    FPS = 10  # Set a stable FPS to prevent fast playback

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            if frame_count % FRAME_SKIP != 0:
                continue

            detected_faces = []
            results = face_detector(frame)
            
            for result in results:
                boxes = result.boxes.xyxy.cpu().numpy()
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box)
                    face = frame[y1:y2, x1:x2]
                    
                    rgb_face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)  # Convert before processing
                    results_mesh = face_mesh.process(rgb_face)
                    if results_mesh.multi_face_landmarks:
                        landmarks = results_mesh.multi_face_landmarks[0].landmark
                        face = align_face(face, landmarks, face.shape[1], face.shape[0])
                    
                    face = cv2.resize(face, (160, 160))
                    face = np.transpose(face, (2, 0, 1))
                    face = (face / 255.0 - 0.5) / 0.5

                    img_embedding = encode(face).detach().numpy().flatten()
                    detect_dict = {k: min([cosine(v, img_embedding) for v in data["embeddings"]])
                                   for k, data in face_recognition.all_people_faces.items() if data["embeddings"]}

                    if not detect_dict or min(detect_dict.values()) >= 0.5:
                        min_key, image_url, value = "Undetected", "N/A", "0.00"
                    else:
                        min_key = min(detect_dict, key=detect_dict.get)
                        image_url = face_recognition.all_people_faces[min_key]["image_url"]
                        value = face_recognition.all_people_faces[min_key].get("value", "0.00")

                    detected_faces.append({"name": min_key, "image_url": image_url, "value": value})

            people_count = len(detected_faces)
            loop = asyncio.get_running_loop()
            current_time = loop.time()

            if people_count >= 1:
                if people_detected_start is None:
                    people_detected_start = current_time

                if current_time - people_detected_start >= 7:
                    if func.notify:
                        message = json.dumps({"timestamp": int(current_time), "people_count": people_count})
                        try:
                            rabbitmq_channel.basic_publish(exchange="", routing_key="face_notifications", body=message)
                        except Exception as e:
                            print("RabbitMQ Error:", str(e))

                    if func.saveRecordings and not recording:
                        file_name = f"{func.name}_{int(datetime.now().timestamp())}.mp4"
                        file_path = os.path.join("storage", "recordings", file_name)
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        
                        if frame.shape[0] > 0 and frame.shape[1] > 0:
                            height, width, _ = frame.shape
                            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                            out = cv2.VideoWriter(file_path, fourcc, FPS, (width, height))
                            recording = True
                            recording_start_time = current_time
                            print(f"🔴 Recording started: {file_path}")
                        else:
                            print("⚠️ Frame size invalid. Skipping recording.")

                if recording and out and out.isOpened():
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Fix color issue
                    out.write(frame_bgr)

            else:
                if recording:
                    if recording_start_time and current_time - recording_start_time >= 5:
                        print(f"🛑 Stopping recording: {file_path}")
                        out.release()
                        recording = False
                        out = None
                        recording_start_time = None
                
                people_detected_start = None

            people_count_log.append(people_count)
            if len(people_count_log) >= 10 * 60 / 5:
                avg_count = sum(people_count_log) / len(people_count_log)
                new_info = FunctionInfo(function_id=func.id, timestamp=datetime.now(), avg_people_count=avg_count)
                session.add(new_info)
                session.commit()
                people_count_log.clear()

            await asyncio.sleep(1 / FPS)  # Maintain stable FPS

    except Exception as e:
        print(f"Error in face detection: {str(e)}")
    finally:
        if out:
            print(f"🛑 Stopping recording: {file_path}")
            out.release()
        cap.release()