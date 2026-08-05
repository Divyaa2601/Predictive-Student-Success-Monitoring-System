import os
import sys

import mysql.connector
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash


# =========================================================
# PROJECT PATH
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

load_dotenv(
    os.path.join(BASE_DIR, ".env")
)


# =========================================================
# DATABASE CONNECTION
# =========================================================

connection = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 3306)),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

cursor = connection.cursor()


# =========================================================
# DEMO ACCOUNT PASSWORDS
# =========================================================

accounts = {
    "faculty01": "Faculty@123",
    "student01": "Student@123",
    "student02": "Student@123",
    "student03": "Student@123"
}


# =========================================================
# HASH AND UPDATE PASSWORDS
# =========================================================

for username, password in accounts.items():

    password_hash = generate_password_hash(
        password
    )

    cursor.execute(
        """
        UPDATE users
        SET password_hash = %s
        WHERE username = %s;
        """,
        (
            password_hash,
            username
        )
    )


connection.commit()

cursor.close()
connection.close()


print("=" * 50)
print("PASSWORD SETUP COMPLETED")
print("=" * 50)

print("\nDemo accounts updated successfully.")

print("\nFaculty:")
print("Username: faculty01")
print("Password: Faculty@123")

print("\nStudents:")
print("Username: student01 / student02 / student03")
print("Password: Student@123")