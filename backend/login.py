import sys
import mysql.connector

def student_login(username, password):
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Ahmed@1882003",
            database="smart_attendance"
        )
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM students WHERE email=%s AND password=%s",
            (username, password)
        )
        student = cursor.fetchone()
        if student:
            return "Login successful"
        else:
            return "Login failed"
    except mysql.connector.Error as e:
        return f"Error: {e}"
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals() and db.is_connected():
            db.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python login.py <username> <password>")
    else:
        username = sys.argv[1]
        password = sys.argv[2]
        print(student_login(username, password))
