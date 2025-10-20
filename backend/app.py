# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import os
from dotenv import load_dotenv
from datetime import datetime, time, timedelta

# Load environment variables from .env
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Ahmed@1882003")
DB_NAME = os.getenv("DB_NAME", "smart_attendance")

app = Flask(__name__)
CORS(app)  # allow React frontend to call backend

# -----------------------------
# Database connection helper
# -----------------------------
def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

# -----------------------------
# Student Login
# -----------------------------
@app.route('/student-login', methods=['POST'])
def student_login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT student_id, name FROM students WHERE email=%s AND password=%s",
            (username, password)
        )
        student = cursor.fetchone()
        if student:
            return jsonify({"message": "Login successful", "student_id": student["student_id"], "name": student["name"]})
        else:
            return jsonify({"message": "Login failed"}), 401

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals() and db.is_connected():
            db.close()

# -----------------------------
# Admin Login
# -----------------------------
@app.route('/admin-login', methods=['POST'])
def admin_login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM admins WHERE email=%s AND password=%s",
            (username, password)
        )
        admin = cursor.fetchone()
        if admin:
            return jsonify({"message": "Login successful"})
        else:
            return jsonify({"message": "Login failed"})
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"})
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals() and db.is_connected():
            db.close()

# -----------------------------
# Add Class
# -----------------------------
@app.route('/add-class', methods=['POST'])
def add_class():
    try:
        data = request.get_json()
        day = data.get("day")
        period = data.get("period")
        course_code = data.get("course_code")
        room = data.get("room")

        if not all([day, period, course_code, room]):
            return jsonify({"error": "Missing required fields"}), 400

        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO timetable (day, period, course_code, room)
            VALUES (%s, %s, %s, %s)
        """, (day, period, course_code, room))
        db.commit()

        return jsonify({"message": "Class added successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals() and db.is_connected():
            db.close()



# -----------------------------
# Remove Class
# -----------------------------
@app.route('/remove-class', methods=['POST'])
def remove_class():
    try:
        data = request.get_json()
        day = data.get("day")
        period = data.get("period")

        if not all([day, period]):
            return jsonify({"error": "Missing required fields"}), 400

        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("""
            DELETE FROM timetable
            WHERE day=%s AND period=%s
        """, (day, period))
        db.commit()

        return jsonify({"message": "Class removed successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals() and db.is_connected():
            db.close()



# -----------------------------
# Get Timetables with Course Name
# -----------------------------
@app.route('/get-timetable', methods=['GET'])
def get_timetable():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id, course_code, day, period, room FROM timetable ORDER BY day, period")
        timetable = cursor.fetchall()
        return jsonify(timetable)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals() and db.is_connected():
            db.close()





# -----------------------------
# Mark Attendance
# -----------------------------
@app.route('/mark-attendance', methods=['POST'])
def mark_attendance():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        now = datetime.now()
        day = now.strftime("%A")
        current_time = now.time()

        # Determine current period by time ranges
        period_times = {
            1: ("09:00:00", "09:50:00"),
            2: ("10:00:00", "10:50:00"),
            3: ("11:00:00", "11:50:00"),
            4: ("12:00:00", "12:50:00"),
            5: ("13:00:00", "13:50:00"),
            6: ("14:00:00", "14:50:00"),
            7: ("15:00:00", "15:50:00"),
            8: ("16:00:00", "16:50:00"),
        }

        current_period = None
        from datetime import datetime as _dt
        for p, (s, e) in period_times.items():
            start = _dt.strptime(s, "%H:%M:%S").time()
            end = _dt.strptime(e, "%H:%M:%S").time()
            if start <= current_time <= end:
                current_period = p
                break

        if current_period is None:
            return jsonify({"message": "No class running at this time"}), 400

        # Get course for this period
        cursor.execute("""
            SELECT course_code FROM timetable
            WHERE day=%s AND period=%s
            LIMIT 1
        """, (day, current_period))
        course_row = cursor.fetchone()
        if not course_row:
            return jsonify({"message": "No course scheduled right now"}), 400
        course_code = course_row["course_code"]

        # Load enrolled students
        cursor.execute("""
            SELECT student_id FROM student_attendance
            WHERE course_code=%s
        """, (course_code,))
        enrolled_students = [r["student_id"] for r in cursor.fetchall()]

        # Run face recognizer
        from recognizer import main as recognizer_main
        recognizer_main()

        import json
        with open("attendance.json", "r") as f:
            attendance_data = json.load(f)

        students_present = set(attendance_data.get("present", []))

        # Update only the students who are present
        for student_id in enrolled_students:
            attended = 1 if student_id in students_present else 0
            cursor.execute("""
                UPDATE student_attendance
                SET attendance_count = attendance_count + %s
                WHERE student_id=%s AND course_code=%s
            """, (attended, student_id, course_code))

        # Increment class count for the course
        cursor.execute("""
            UPDATE courses
            SET class_count = class_count + 1
            WHERE course_code=%s
        """, (course_code,))

        db.commit()

        # Compute attendance summary
        cursor.execute("""
            SELECT sa.student_id, sa.attendance_count, c.class_count
            FROM student_attendance sa
            JOIN courses c ON sa.course_code = c.course_code
            WHERE sa.course_code = %s
        """, (course_code,))
        rows = cursor.fetchall()

        num_attendees = len([r for r in rows if r["student_id"] in students_present])
        num_absents = len(rows) - num_attendees

        attendance_percentages = {
            r["student_id"]: int((r["attendance_count"] / r["class_count"]) * 100) if r["class_count"] > 0 else 0
            for r in rows
        }

        return jsonify({
            "course": course_code,
            "attendees": num_attendees,
            "absents": num_absents,
            "percentages": attendance_percentages
        })

    except Exception as e:
        print("[ERROR] mark-attendance:", str(e))
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals() and db.is_connected():
            db.close()



# -----------------------------
# Student Dashboard
# -----------------------------
@app.route('/student-dashboard/<student_id>', methods=['GET'])
def student_dashboard(student_id):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT name, student_id, profile_picture FROM students WHERE student_id=%s",
            (student_id,)
        )
        student = cursor.fetchone()
        if not student:
            return jsonify({"error": "Student not found"}), 404

        cursor.execute("""
            SELECT sa.course_code, sa.attendance_count, c.class_count
            FROM student_attendance sa
            JOIN courses c ON sa.course_code = c.course_code
            WHERE sa.student_id = %s
        """, (student_id,))
        attendance_rows = cursor.fetchall()
        attendance_data = []
        for row in attendance_rows:
            class_count = row["class_count"] if row["class_count"] else 1
            percentage = int((row["attendance_count"] / class_count) * 100) if class_count > 0 else 0
            attendance_data.append({
                "course": row["course_code"],
                "attendance": percentage
            })

        cursor.execute("""
            SELECT t.day, t.course_code as subject, CONCAT('Period ', t.period) as time
            FROM timetable t
            JOIN student_attendance sa ON sa.course_code = t.course_code
            WHERE sa.student_id=%s
         """, (student_id,))
        timetable = cursor.fetchall()

        return jsonify({
            "student": student,
            "attendanceData": attendance_data,
            "timetable": timetable
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals() and db.is_connected():
            db.close()

# -----------------------------
# Test route
# -----------------------------
@app.route('/')
def index():
    return "Smart Attendance Backend Running"

# -----------------------------
# Get Students (used by Admin UI)
# -----------------------------
@app.route('/get-students', methods=['GET'])
def get_students():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT student_id, name, email, profile_picture FROM students ORDER BY student_id")
        students = cursor.fetchall()
        return jsonify({"students": students})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals() and db.is_connected():
            db.close()

# -----------------------------
# Add Student (multipart/form-data)
# -----------------------------
@app.route('/add-student', methods=['POST'])
def add_student():
    try:
        # Expect multipart form: student_id, name, email, password and optional profile_pic file
        student_id = request.form.get("student_id")
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        file = request.files.get("profile_pic")

        if not all([student_id, name, email, password]):
            return jsonify({"error": "Missing required fields"}), 400

        # Save profile picture to known_faces
        profile_path = None
        if file:
            from werkzeug.utils import secure_filename
            filename = secure_filename(f"{student_id}.jpg")
            faces_dir = os.path.join(os.getcwd(), "known_faces")
            os.makedirs(faces_dir, exist_ok=True)
            save_path = os.path.join(faces_dir, filename)
            file.save(save_path)
            profile_path = save_path  # store absolute or relative path as you prefer

            # Create face encoding immediately and save to known_encodings
            try:
                import face_recognition
                import numpy as np
                image = face_recognition.load_image_file(save_path)
                locations = face_recognition.face_locations(image)
                if len(locations) == 1:
                    encoding = face_recognition.face_encodings(image, locations)[0]
                    enc_dir = os.path.join(os.getcwd(), "known_encodings")
                    os.makedirs(enc_dir, exist_ok=True)
                    np.save(os.path.join(enc_dir, f"{student_id}.npy"), encoding)
                else:
                    print(f"Warning: expected 1 face for {student_id}, found {len(locations)}")
            except Exception as e:
                print("Failed to create encoding:", e)

        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("INSERT INTO students (student_id, name, email, password, profile_picture) VALUES (%s,%s,%s,%s,%s)",
                       (student_id, name, email, password, profile_path))
        db.commit()
        return jsonify({"message": "Student added successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals() and db.is_connected():
            db.close()

# -----------------------------
# Delete Student (by student_id)
# -----------------------------
@app.route('/delete-student/<student_id>', methods=['DELETE'])
def delete_student(student_id):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        # Delete the student by student_id column, not id
        cursor.execute("DELETE FROM students WHERE student_id = %s", (student_id,))
        db.commit()
        return jsonify({"message": "Student deleted successfully"})
    except Exception as e:
        print("[ERROR] delete-student:", e)
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals() and db.is_connected():
            db.close()


if __name__ == "__main__":
    app.run(debug=True)