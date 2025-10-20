import face_recognition
import cv2
import numpy as np
import os
import json
import mysql.connector
from datetime import datetime
import os

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Ahmed@1882003")
DB_NAME = os.getenv("DB_NAME", "smart_attendance")

def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

# -----------------------------
# Get current course by period
# -----------------------------
def get_current_course():
    now = datetime.now()
    day = now.strftime("%A")
    current_hour = now.hour
    current_minute = now.minute

    # Map periods 1–8 to start/end times
    period_times = {
        1: ("09:00", "09:50"),
        2: ("10:00", "10:50"),
        3: ("11:00", "11:50"),
        4: ("12:00", "12:50"),
        5: ("13:00", "13:50"),
        6: ("14:00", "14:50"),
        7: ("15:00", "15:50"),
        8: ("16:00", "16:50"),
    }

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    for period, (start_str, end_str) in period_times.items():
        start_hour, start_min = map(int, start_str.split(":"))
        end_hour, end_min = map(int, end_str.split(":"))
        start_time = datetime(now.year, now.month, now.day, start_hour, start_min)
        end_time = datetime(now.year, now.month, now.day, end_hour, end_min)

        if start_time <= now <= end_time:
            # find course for this period
            cursor.execute("""
                SELECT course_code FROM timetable
                WHERE day=%s AND period=%s
                LIMIT 1
            """, (day, period))
            course = cursor.fetchone()
            cursor.close()
            db.close()
            return course["course_code"] if course else None

    cursor.close()
    db.close()
    return None

# -----------------------------
# Load enrolled students & known encodings
# -----------------------------
def load_known_faces(course_code):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT sa.student_id
        FROM student_attendance sa
        WHERE sa.course_code=%s
    """, (course_code,))
    rows = cursor.fetchall()
    cursor.close()
    db.close()

    known_encodings = []
    student_ids = []

    for row in rows:
        student_id = row["student_id"]
        encoding_path = f"known_encodings/{student_id}.npy"
        if os.path.exists(encoding_path):
            known_encodings.append(np.load(encoding_path))
            student_ids.append(student_id)
        else:
            print(f"⚠️ Encoding not found for {student_id}")

    return student_ids, known_encodings

# -----------------------------
# Face recognition main
# -----------------------------
def main():
    course_code = get_current_course()
    if not course_code:
        print("No course scheduled right now.")
        with open("attendance.json", "w") as f:
            json.dump({"present": []}, f)
        return

    student_ids, known_encodings = load_known_faces(course_code)
    if not known_encodings:
        print("No known face encodings for this course.")
        with open("attendance.json", "w") as f:
            json.dump({"present": []}, f)
        return

    # Capture frame from camera
    video_capture = cv2.VideoCapture(0)
    ret, frame = video_capture.read()
    video_capture.release()

    if not ret:
        print("⚠️ Failed to capture frame")
        with open("attendance.json", "w") as f:
            json.dump({"present": []}, f)
        return

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    present_students = set()  # use set to avoid duplicates

    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.45)
        face_distances = face_recognition.face_distance(known_encodings, face_encoding)

        if True in matches:
            best_match_index = np.argmin(face_distances)
            present_students.add(student_ids[best_match_index])

    present_students = list(present_students)
    print(f"Detected faces: {len(face_encodings)}")
    print(f"Attendance recorded: {present_students}")

    # Save attendance
    with open("attendance.json", "w") as f:
        json.dump({"present": present_students}, f)

if __name__ == "__main__":
    main()