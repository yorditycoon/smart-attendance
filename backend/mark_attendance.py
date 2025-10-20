import sys
import mysql.connector
import subprocess
import json
from datetime import datetime

def get_current_course(db):
    now = datetime.now()
    day = now.strftime("%A")
    current_time = now.strftime("%H:%M:%S")
    try:
        cursor = db.cursor(dictionary=True)
        query = """
        SELECT course_code 
        FROM timetable 
        WHERE day=%s AND start_time <= %s AND end_time >= %s
        LIMIT 1
        """
        cursor.execute(query, (day, current_time, current_time))
        result = cursor.fetchone()
        return result['course_code'] if result else None
    finally:
        cursor.close()

def run_recognizer():
    subprocess.run(['python', 'recognizer.py'], check=True)

def update_attendance(db, course_code):
    with open("attendance.json", "r") as f:
        attendance_data = json.load(f)

    students_present = attendance_data.get("present", [])
    num_attendees = len(students_present)

    try:
        cursor = db.cursor()
        for student_id in students_present:
            cursor.execute("""
                UPDATE student_attendance
                SET attendance_count = attendance_count + 1
                WHERE student_id=%s AND course_code=%s
            """, (student_id, course_code))

        cursor.execute("""
            UPDATE courses
            SET class_count = class_count + 1
            WHERE course_code=%s
        """, (course_code,))
        db.commit()

        cursor.execute("SELECT COUNT(*) FROM student_attendance WHERE course_code=%s", (course_code,))
        total_students = cursor.fetchone()[0]
        num_absent = total_students - num_attendees
        return num_attendees, num_absent
    finally:
        cursor.close()

def main():
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Ahmed@1882003",
            database="smart_attendance"
        )

        course_code = get_current_course(db)
        if not course_code:
            print("No course scheduled right now.")
            return

        run_recognizer()
        attendees, absents = update_attendance(db, course_code)

        print(f"Course: {course_code}")
        print(f"Number of attendees: {attendees}")
        print(f"Number of absents: {absents}")

    except mysql.connector.Error as e:
        print(f"Database Error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'db' in locals() and db.is_connected():
            db.close()

if __name__ == "__main__":
    main()
