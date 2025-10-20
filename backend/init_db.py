import mysql.connector
import os
import sys
from mysql.connector import errorcode

# -----------------------------
# Config
# -----------------------------
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "Ahmed@1882003"
DB_NAME = "smart_attendance"
SQL_FILE = os.path.join(os.getcwd(), "smart_attendance.sql")

# -----------------------------
# Connect to MySQL server
# -----------------------------
try:
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cursor = conn.cursor()
    print("[INFO] Connected to MySQL server.")
except mysql.connector.Error as err:
    print(f"[ERROR] Could not connect to MySQL: {err}")
    sys.exit(1)

# -----------------------------
# Create database if not exists
# -----------------------------
try:
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    print(f"[INFO] Database '{DB_NAME}' is ready.")
except mysql.connector.Error as err:
    print(f"[ERROR] Failed creating database: {err}")
    sys.exit(1)

# -----------------------------
# Use the database
# -----------------------------
try:
    conn.database = DB_NAME
except mysql.connector.Error as err:
    print(f"[ERROR] Database {DB_NAME} does not exist.")
    sys.exit(1)

# -----------------------------
# Import SQL file
# -----------------------------
if not os.path.exists(SQL_FILE):
    print(f"[ERROR] SQL file '{SQL_FILE}' not found.")
    sys.exit(1)

print(f"[INFO] Importing '{SQL_FILE}' ...")
with open(SQL_FILE, "r", encoding="utf-16") as f:
    sql_commands = f.read().split(";")

for command in sql_commands:
    command = command.strip()
    if command:
        try:
            cursor.execute(command)
        except mysql.connector.Error as err:
            print(f"[WARNING] Skipping command due to error: {err}")

conn.commit()
cursor.close()
conn.close()
print("[SUCCESS] Database initialized successfully.")
