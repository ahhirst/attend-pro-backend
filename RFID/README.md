import mysql.connector
from datetime import datetime

# Database connection
connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="your_password",
    database="your_database"
)

cursor = connection.cursor()

def update_class_count(rfid_card_id):
    # Get the current date and time
    current_time = datetime.now().time()
    current_date = datetime.now().date()
    
    # Fetch the schedule to check if the scan is within a class time
    cursor.execute("SELECT subject_id, subject_name, start_time, end_time FROM class_schedule")
    schedule = cursor.fetchall()
    
    for subject_id, subject_name, start_time, end_time in schedule:
        # Check if the current time falls within the class timing
        if start_time <= current_time <= end_time:
            # Check if the class has already been logged for today
            cursor.execute("""
                SELECT * FROM class_log
                WHERE subject_id = %s AND class_date = %s
            """, (subject_id, current_date))
            class_logged = cursor.fetchone()

            if not class_logged:
                # Log the class in class_log
                cursor.execute("""
                    INSERT INTO class_log (subject_id, class_date)
                    VALUES (%s, %s)
                """, (subject_id, current_date))
                connection.commit()

                # Increment the total classes in classes_conducted
                cursor.execute("""
                    UPDATE classes_conducted 
                    SET total_classes = total_classes + 1 
                    WHERE subject_id = %s
                """, (subject_id,))
                connection.commit()

                print(f"Total class count updated for {subject_name}.")
            else:
                print(f"Class already logged for {subject_name} today.")

            # Break after updating or checking the current class
            return

    print("RFID scan occurred outside of class hours.")

# Example: Simulate an RFID scan
update_class_count(rfid_card_id="123456")

# Close the connection
cursor.close()
connection.close()








Class Schedule (class_schedule):

subject_id	subject_name	start_time	end_time
1	Mathematics	09:00:00	10:00:00
Classes Conducted (classes_conducted):

subject_id	subject_name	total_classes
1	Mathematics	20
Class Log (class_log):

log_id	subject_id	class_date
1	1	2024-12-21
