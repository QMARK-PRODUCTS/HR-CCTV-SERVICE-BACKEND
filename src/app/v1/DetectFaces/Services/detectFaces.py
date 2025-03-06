import pickle, os , cv2
from scipy.spatial.distance import cosine
import mediapipe as mp
from collections import deque, Counter
from ultralytics import YOLO
import torch
from facenet_pytorch import InceptionResnetV1
import numpy as np

VOTE_WINDOW = 10  # Number of frames for stabilization
FRAME_SKIP = 3  # Analyze every 3rd frame for efficiency
face_vote_memory = {}  # Dictionary to store recent predictions
MODELS_DIR = f"{os.getenv('STORAGE_DIR', './storage')}/models/"

face_detector = YOLO('yolov8n-face.pt')  # Use a face-specific YOLOv8 model

resnet = InceptionResnetV1(pretrained='vggface2').eval()

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=10, min_detection_confidence=0.5)

# Load saved face embeddings from pickle file
def load_face_embeddings():
    with open(MODELS_DIR + 'allFaces.pkl', 'rb') as f:
        return pickle.load(f)

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

# Modify the detect function to use the loaded face embeddings
def detect(cam=0, thres=0.5, switch_threshold=35):
    all_people_faces = load_face_embeddings()
    vdo = cv2.VideoCapture(cam)
    stable_identities = {}
    frame_count = 0
    detected_urls = []  # To store detected image URLs for display

    while vdo.grab():
        frame_count += 1
        if frame_count % FRAME_SKIP != 0:
            continue  # Skip frames for efficiency
        
        _, img0 = vdo.retrieve()
        scale_percent = 50
        width = int(img0.shape[1] * scale_percent / 100)
        height = int(img0.shape[0] * scale_percent / 100)
        img0 = cv2.resize(img0, (width, height))

        detected_urls.clear()  # Clear detected URLs for the new frame

        results = face_detector(img0)
        for result in results:
            boxes = result.boxes.xyxy.cpu().numpy()
            for box in boxes:
                x1, y1, x2, y2 = map(int, box)
                face = img0[y1:y2, x1:x2]
                
                rgb_face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
                results_mesh = face_mesh.process(rgb_face)
                if results_mesh.multi_face_landmarks:
                    landmarks = results_mesh.multi_face_landmarks[0].landmark
                    face = align_face(face, landmarks, face.shape[1], face.shape[0])
                
                face = cv2.resize(face, (160, 160))
                face = np.transpose(face, (2, 0, 1))
                face = (face / 255.0 - 0.5) / 0.5
                
                img_embedding = encode(face).detach().numpy().flatten()
                
                detect_dict = {}
                for k, data in all_people_faces.items():
                    v_list = data.get("embeddings", [])
                    if v_list:  # Only process if embeddings exist
                        min_dist = min([cosine(v, img_embedding) for v in v_list])
                        detect_dict[k] = min_dist
                    else:
                        detect_dict[k] = float('inf')  # Assign a large distance if no embeddings are found

                if not detect_dict:
                    continue
                
                min_key = min(detect_dict, key=detect_dict.get)
                if detect_dict[min_key] >= thres:
                    min_key = 'Undetected'
                    image_url = "N/A"
                else:
                    image_url = all_people_faces[min_key]["image_url"]
                    detected_urls.append(image_url)  # Store detected image URL

                face_id = (x1, y1, x2, y2)
                if face_id not in face_vote_memory:
                    face_vote_memory[face_id] = deque(maxlen=VOTE_WINDOW)
                
                face_vote_memory[face_id].append(min_key)
                most_common_label, count = Counter(face_vote_memory[face_id]).most_common(1)[0]
                
                if face_id not in stable_identities:
                    stable_identities[face_id] = {"label": most_common_label, "count": 0}
                
                if stable_identities[face_id]["label"] == most_common_label:
                    stable_identities[face_id]["count"] += 1
                else:
                    stable_identities[face_id]["count"] = 0
                
                if stable_identities[face_id]["count"] >= switch_threshold:
                    stable_identities[face_id]["label"] = most_common_label
                
                final_label = stable_identities[face_id]["label"]

                # Draw bounding box and label
                cv2.rectangle(img0, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(img0, final_label, (x1, y1 - 10),  # Name above the rectangle
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

        # Display image URLs in the top-left corner
        y_offset = 20
        for url in detected_urls:
            cv2.putText(img0, url, (10, y_offset), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
            y_offset += 15  # Move text down for next URL

        cv2.imshow("output", img0)
        if cv2.waitKey(1) == ord('q'):
            cv2.destroyAllWindows()
            break

if __name__ == "__main__":
    detect(0)