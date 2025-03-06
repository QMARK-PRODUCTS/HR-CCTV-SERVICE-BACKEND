import os
import cv2
import torch
import pickle
from facenet_pytorch import InceptionResnetV1
from ultralytics import YOLO
import numpy as np
import mediapipe as mp

USER_STORAGE_DIR = f"{os.getenv('STORAGE_DIR', './storage')}/users/"
MODELS_DIR = f"{os.getenv('STORAGE_DIR', './storage')}/models/"
LABELS_FILE = os.path.join(USER_STORAGE_DIR, "labels.txt")

### Load YOLOv8 model for face detection
face_detector = YOLO('yolov8n-face.pt')

### Load FaceNet model for face recognition
resnet = InceptionResnetV1(pretrained='vggface2').eval()

### Load Mediapipe for face alignment
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=10, min_detection_confidence=0.5)

# Helper function to encode faces
def encode(img):
    img = torch.Tensor(img).unsqueeze(0)  # Add batch dimension
    if img.shape[1] != 3:  # Ensure the image is in (C, H, W) format
        img = img.permute(0, 3, 1, 2)
    res = resnet(img)
    return res

# Helper function to align faces using Mediapipe landmarks
def align_face(image, landmarks, image_width, image_height):
    left_eye = landmarks[159]
    right_eye = landmarks[386]
    left_eye_x = int(left_eye.x * image_width)
    left_eye_y = int(left_eye.y * image_height)
    right_eye_x = int(right_eye.x * image_width)
    right_eye_y = int(right_eye.y * image_height)
    
    dY = right_eye_y - left_eye_y
    dX = right_eye_x - left_eye_x
    angle = np.degrees(np.arctan2(dY, dX)) - 180
    
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    aligned_face = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC)
    
    return aligned_face

# Function to extract frames from video
def extract_frames(video_path, frame_interval=10):
    frames = []
    cap = cv2.VideoCapture(video_path)
    count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if count % frame_interval == 0:
            frames.append(frame)
        count += 1
    cap.release()
    return frames

def get_labels():
    labels = []
    if os.path.exists(LABELS_FILE):
        with open(LABELS_FILE, "r") as file:
            for line in file:
                parts = line.strip().split(",")
                if len(parts) == 3:
                    labels.append((parts[0], parts[1], parts[2]))  # (folder_name, name, image_url)
    return labels
# Train function to process photos and videos and save embeddings
def TrainFaces():
    all_people_faces = {}
    labels = get_labels()
    
    for folder_name, person_name, image_url in labels:
        person_folder = os.path.join(USER_STORAGE_DIR, folder_name)
        if os.path.isdir(person_folder):
            all_people_faces[person_name] = {"image_url": image_url, "embeddings": []}
            
            image_path = os.path.join(person_folder, "profile.jpeg")
            
            if os.path.exists(image_path):
                img = cv2.imread(image_path)
                if img is not None:
                    results = face_detector(img)
                    for result in results:
                        boxes = result.boxes.xyxy.cpu().numpy()
                        for box in boxes:
                            x1, y1, x2, y2 = map(int, box)
                            face = img[y1:y2, x1:x2]
                            
                            rgb_face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
                            results_mesh = face_mesh.process(rgb_face)
                            if results_mesh.multi_face_landmarks:
                                landmarks = results_mesh.multi_face_landmarks[0].landmark
                                face = align_face(face, landmarks, face.shape[1], face.shape[0])
                            
                            face = cv2.resize(face, (160, 160))
                            face = np.transpose(face, (2, 0, 1))
                            face = (face / 255.0 - 0.5) / 0.5
                            
                            encoded_face = encode(face)
                            all_people_faces[person_name]["embeddings"].append(encoded_face.detach().numpy().flatten())

    
            
            # Process video
            video_path = os.path.join(person_folder, "video.mp4")
            if os.path.exists(video_path):
                frames = extract_frames(video_path, frame_interval=10)
                for frame in frames:
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
                            
                            encoded_face = encode(face)
                            all_people_faces[person_name].append(encoded_face.detach().numpy().flatten())

    # Save embeddings to a pickle file
    with open(MODELS_DIR + "allFaces.pkl", 'wb') as f:
        pickle.dump(all_people_faces, f)

if __name__ == "__main__":
    TrainFaces()