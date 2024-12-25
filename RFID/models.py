import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='root@123',
        database='Attendance'
    )

def register_student(name, enrollment_no, phone_no, email, password, address):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # hashed_password = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO registration (name, enrollment_no, phone_no, email, password, address) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (name, enrollment_no, phone_no, email, password, address)
        )
        connection.commit()
    except mysql.connector.Error as e:
        connection.rollback()
        raise e
    finally:
        connection.close()

def authenticate_user(enrollment_no, password):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        query="SELECT * FROM registration WHERE enrollment_no = %s AND password=%s"
        cursor.execute(query,(enrollment_no,password))
        user = cursor.fetchone()
        return user

    except mysql.connector.Error as e:
        raise e
    finally:
        connection.close()

def fetch_student_by_id(student_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT name, phone_no, email, address FROM registration WHERE enrollment_no = %s", (student_id))
    student = cursor.fetchone()
    for i in student:
        print(i)
    connection.close()
    return student

def fetch_student_by_enrollment(enrollment_no):
    connection = get_db_connection()  # This connects to your MySQL database
    cursor = connection.cursor(dictionary=True)  # Use dictionary=True for better readability
    try:
        # Query to fetch a student by enrollment number
        query = "SELECT * FROM registration WHERE enrollment_no = %s"
        cursor.execute(query, (enrollment_no,))
        student = cursor.fetchone()  # Fetch one record
        return student  # Returns the student record as a dictionary or None if not found
    except mysql.connector.Error as e:
        print(f"Error fetching student: {e}")
        raise e  # Rethrow the exception to handle it in the calling function
    finally:
        connection.close()  # Always close the connection

def check_db_connection():
    try:
        connection = get_db_connection()
        if connection.is_connected():
            return True, "Database connection successful."
    except mysql.connector.Error as e:
        return False, f"Database connection failed: {e}"
    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()

def fetch_all_students():
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM registration")
        rows = cursor.fetchall()  # Fetch all rows
        return rows
    except mysql.connector.Error as e:
        raise e
    finally:
        connection.close()
