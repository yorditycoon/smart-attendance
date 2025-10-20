# create_encodings.py
import face_recognition
import cv2
import os
import numpy as np

# Folder containing student images
# Structure: known_faces_raw/S101.jpg, known_faces_raw/S102.jpg, etc.
RAW_FACES_DIR = "known_faces"
# Folder to save encodings
ENCODINGS_DIR = "known_encodings"

os.makedirs(ENCODINGS_DIR, exist_ok=True)

# Loop through all student images
for file_name in os.listdir(RAW_FACES_DIR):
    if file_name.lower().endswith((".jpg", ".jpeg", ".png")):
        student_id = os.path.splitext(file_name)[0]  # S101, S102, etc.
        img_path = os.path.join(RAW_FACES_DIR, file_name)
        image = face_recognition.load_image_file(img_path)

        # Detect face locations
        face_locations = face_recognition.face_locations(image)
        if len(face_locations) != 1:
            print(f"⚠️ {student_id}: Expected 1 face, found {len(face_locations)}. Skipping...")
            continue

        # Get face encoding
        face_encoding = face_recognition.face_encodings(image, face_locations)[0]

        # Save encoding as .npy
        encoding_path = os.path.join(ENCODINGS_DIR, f"{student_id}.npy")
        np.save(encoding_path, face_encoding)
        print(f"✅ Saved encoding for {student_id}")
