# import serial
# import mysql.connector
# import time
# from datetime import datetime



# # Function to connect to the MySQL database
# def get_db_connection():
#     try:
#         connection = mysql.connector.connect(
#             host="localhost",
#             user="root",            # Replace with your MySQL username
#             password="root@123",  # Replace with your MySQL password
#             database="attendance"  # Replace with your database name
#         )
#         return connection
#     except mysql.connector.Error as e:
#         print(f"Error connecting to MySQL: {e}")
#         return None

# # Function to mark attendance for the student
# # def 
# def mark_attendance(mark,Enrollment):
#     connection = get_db_connection()
#     if connection is None:
#         print("Failed to connect to database.")
#         return
#     cursor = connection.cursor()
#     update_query = "UPDATE registration SET rfid_id = %s WHERE Enrollment_NO = %s"
#     cursor.execute(update_query, (mark,Enrollment))
#     connection.commit()

#     # Check if the student is registered
#     query = "SELECT * FROM registration WHERE Enrollment_NO = %s"
#     cursor.execute(query, (1,))
#     result = cursor.fetchone()
#     # for i in result:
#     print(result)
#     # update_query = "UPDATE registration SET rfid_tag = %s WHERE Enrollment_NO = %s"
#     # update_query = "UPDATE registration SET rfid_tag = %s WHERE Enrollment_NO = %s"
#     # attendance_query = """
#     #         INSERT INTO attendance (enrollment_NO, attendance_date)
#     #         SELECT %s, CURRENT_DATE()
#     #         WHERE NOT EXISTS (
#     #             SELECT 1 FROM attendance 
#     #             WHERE enrollment_NO = %s AND attendance_date = CURRENT_DATE()
#     #         )
#     #     """
#     # # cursor.execute(attendance_query, (enrollment, enrollment))
#     # connection.commit()
   
# try:
#     ser = serial.Serial('COM5', 9600, timeout=1)  # Replace with your correct port
#     print("Connected to serial port...")
# except serial.SerialException as e:
#     print(f"Error connecting to serial port: {e}")
#     exit()

# # Function to continuously read RFID tags
# def read_rfid():
#     try:
#         while True:
#             if ser.in_waiting > 0:
#                 rfid_tag = ser.readline().decode('utf-8').strip()  # Read and decode the RFID tag
#                 print(f"RFID Tag Detected: {rfid_tag}")
#                 # u=input('Enter Roll no')
                
#                 mark_attendance(rfid_tag,60)
#                 # no(rfid_tag)# Mark attendance in the database
#                 time.sleep(5)  # Wait before scanning the next tag
#     except KeyboardInterrupt:
#         print("Terminating the attendance system.")
#     except Exception as e:
#         print(f"Error reading RFID: {e}")
#     finally:
#         # Cleanup resources
#         if ser.is_open:
#             ser.close()
#         print("Serial port closed.")

# # Start the attendance system
# print("Attendance system started. Waiting for RFID tags...")
# read_rfid()


from flask import jsonify, request
import serial
import time
import mysql.connector
from mysql.connector import Error
from datetime import datetime

# Set up the serial connection (update COM port to match your system)
arduino_port = 'COM5'  # Update this to your Arduino's port
baud_rate = 9600       # Must match the baud rate in the Arduino code

# Database connection parameters
db_config = {
    'host': 'localhost',  # Change to your database host
    'user': 'root',       # Change to your database username
    'password': 'root@123',  # Change to your database password
    'database': 'attendance'
}

# Function to connect to the database
def connect_to_database():
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            print("Connected to the database")
        return connection
    except Error as e:
        print(f"Error connecting to database: {e}")
        return None

# Function to determine the current subject based on time
def get_current_subject(connection):
    try:
        cursor = connection.cursor(dictionary=True)
        current_time = datetime.now().strftime('%H:%M:%S')

        # Query to find the subject based on the current time
        query = """
        SELECT subject_code FROM subject
        WHERE start_time <= %s AND end_time >= %s
        LIMIT 1
        """
        cursor.execute(query, (current_time, current_time))
        subject = cursor.fetchone()

        if subject:
            return subject['subject_code']
        else:
            print("No subject is scheduled at this time.")
            return None
    except Error as e:
        print(f"Database error while fetching subject: {e}")
        return None
    finally:
        cursor.close()
        connection.commit()

def assign_rfid():
    connection = connect_to_database()
    cursor = connection.cursor(dictionary=True)  # Use dictionary=True to fetch results as dictionaries
    
    try:
        # Step 1: Fetch all students with NULL `rfid_id`, ordered alphabetically
        query = "SELECT * FROM registration WHERE rfid_id IS NULL ORDER BY Name ASC;"
        cursor.execute(query)
        students = cursor.fetchall()
        
        if not students:
            return jsonify({"message": "All students already have RFID cards."}), 200
        
        # Step 2: Assign RFID card to the first student
        first_student = students[0]
        new_rfid_id = request.json.get('rfid_id')  # RFID card ID sent via POST request
        
        if not new_rfid_id:
            return jsonify({"error": "RFID card ID is required."}), 400
        
        update_query = "UPDATE registration SET rfid_id = %s WHERE Enrollment_NO = %s;"
        cursor.execute(update_query, (new_rfid_id, first_student['Enrollment_NO']))
        connection.commit()
        
        # Step 3: Return the updated list of students without RFID cards
        cursor.execute(query)
        remaining_students = cursor.fetchall()
        
        return jsonify({
            "message": f"RFID card {new_rfid_id} assigned to {first_student['Name']}.",
            "remaining_students": remaining_students
        }), 200

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

    finally:
        cursor.close()
        connection.close()



# Function to handle RFID card logic and mark attendance
def process_card(uid, connection):
    try:
        cursor = connection.cursor(dictionary=True)

        # Check if the card exists in the registration table
        query = "SELECT * FROM registration WHERE rfid_id = %s"
        cursor.execute(query, (uid,))
        record = cursor.fetchone()

        if record:
            print(f"Card belongs to: {record['Name']}")

            # Determine the current subject based on time
            subject_code = get_current_subject(connection)
            if subject_code is None:
                print("Attendance cannot be marked without a valid subject.")
                return

            student_enrollment = record['enrollment_NO']  # Assuming 'enrollment' is in registration table
            current_time = datetime.now()

            # Insert attendance record
            attendance_query = """
            INSERT INTO attendance (subject_code, enrollment_no, attendance_date, RFID_SCAN , attendance_status)
            VALUES (%s, %s, %s, %s, %s , %s)
            """
            cursor.execute(attendance_query, (
                subject_code,
                student_enrollment,
                'P',
                current_time.strftime('%Y-%m-%d'),
                current_time.strftime('%H:%M:%S')
            ))
            connection.commit()
            print("Attendance marked successfully.")
        else:
            print("Unknown card. Please register the card first.")
            assign_rfid()
            
    except Error as e:
        print(f"Database error: {e}")
    finally:
        cursor.close()


# Main function to read RFID and interact with the database
def read_rfid():
    try:
        # Connect to Arduino
        arduino = serial.Serial(arduino_port, baud_rate, timeout=1)
        print(f"Connected to Arduino on {arduino_port}")

        # Connect to Database
        connection = connect_to_database()
        if connection is None:
            print("Failed to connect to the database. Exiting...")
            return

        while True:
            if arduino.in_waiting > 0:
                data = arduino.readline().decode('utf-8').strip()
                if data.startswith("UID:"):
                    card_uid = data[4:].strip()
                    print(f"Card Scanned: {card_uid}")
                    process_card(card_uid, connection)
    except KeyboardInterrupt:
        print("Exiting script.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'arduino' in locals():
            arduino.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()
        print("Closed connections.")
        

if __name__ == "__main__":
    connect_to_database()
    read_rfid()
# def main():
#     # Main logic of your program
#     print("RFID reader program started.")

# if __name__ == "__main__":
#     main()
