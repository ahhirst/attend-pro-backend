import mysql.connector
from flask import Flask, render_template, request, redirect, session, flash, url_for,jsonify
import os
from datetime import datetime

from datetime import timedelta

# this is flask code

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.permanent_session_lifetime = timedelta(minutes=5)
# session.permanent = True


#Functions to connect to the database
def connect_to_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root@123",
        database="attendance"
        )
def authenticate_user(enrollment_no, password):
    try:
        connection = connect_to_db()
        cursor = connection.cursor()
        query = "SELECT * FROM registration WHERE Enrollment_no = %s AND password = %s"
        # print(session[0],type(session))
        cursor.execute(query, (enrollment_no, password))
        user = cursor.fetchone()
        print(type(user))
        for i in user:
            print(i)
        return user
    except mysql.connector.Error as err:
        print(err)
    finally:
        connection.close()
        cursor.close()
        
def alldata():
    try:
        # Create a database connection
        connection=connect_to_db()
        # Create a cursor object
        cursor = connection.cursor()
        # SQL query to select all data from the table
        query = "SELECT Name,Enrollment_NO,Phone_NO,Email,RFID_ID,Address FROM registration"
        cursor.execute(query)
        # Fetch all the rows from the query
        data = cursor.fetchall()
        # Close the cursor and connection
        cursor.close()
        connection.close()
        print(type(data))
        print(data)
        return data
    except Exception as e:
        return f"Error connecting to the database: {str(e)}", 500
    
def fetch_student_by_enrollment(enrollment_no):
    connection = connect_to_db()  # This connects to your MySQL database
    cursor = connection.cursor(dictionary=True)  # Use dictionary=True for better readability
    try:
        # Query to fetch a student by enrollment number
        query = "SELECT * FROM registration WHERE enrollment_no = %s"
        cursor.execute(query, (enrollment_no,))
        student = cursor.fetchall()  # Fetch one record
        return student  # Returns the student record as a dictionary or None if not found
    except mysql.connector.Error as e:
        print(f"Error fetching student: {e}")
        raise e  # Rethrow the exception to handle it in the calling function
    finally:
        connection.close()  # Always close the connection
    
    
    

@app.route('/')
def index():
    if 'user' in session:
        print(session[0],type(session))
        print('user in session')
        return redirect(url_for('profile'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('profile'))
    if request.method == 'POST':
        # enrollment_no = request.form['enrollment_no']
        # password = request.form['password']
       
        # user = authenticate_user(enrollment_no, password)
        username = request.form['username']
        password = request.form['password']

        connection = connect_to_db()
        cursor = connection.cursor(dictionary=True)

        # Check if the user is a teacher
        cursor.execute("SELECT * FROM teacher WHERE username = %s AND password = %s", (username, password))
        teacher = cursor.fetchone()

        # If teacher credentials are correct, store in session and redirect to teacher portal
        if teacher:
            session['username'] = teacher['username']  # Store username in session
            session['role'] = 'teacher'  # Store role in session (teacher)
            connection = connect_to_db()
            cursor = connection.cursor()
            query = "SELECT * FROM teacher WHERE username = %s AND password = %s"
            # print(session[0],type(session))
            cursor.execute(query, (username, password))
            user = cursor.fetchone()
            print(user,type(user))
            
            return render_template('teacher.html',tech=user)

        # Check if the user is a student
        cursor.execute("SELECT Name,Enrollment_NO,Phone_NO,email,RFID_ID,Address FROM registration WHERE Enrollment_NO = %s AND Password = %s", (username, password))
        student = cursor.fetchone()
        print(student)

        # If student credentials are correct, store in session and redirect to student portal
        if student:
            print('heyyyyyyyyyyyyyyyyyyy')
            print(student,student['Name'])
            values_list = list(student.values())
            print(values_list)
          
            return render_template('student.html',data=values_list)

        # If credentials are incorrect
        return "Invalid username or password, please try again."
    return render_template('login.html')
@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    try:
        # Step 1: Extract data sent from RFID
        enrollment_no = request.json.get('enrollment_no')  # Sent via POST request

        if not enrollment_no:
            return jsonify({"error": "Enrollment number is required"}), 400

        # Step 2: Get current date and time
        current_date = datetime.now().date()
        current_time = datetime.now().strftime('%H:%M:%S')

        # Step 3: Connect to Database
        connection = connect_to_db()
        cursor = connection.cursor()

        # Step 4: Verify enrollment number exists in the registration table
        query = "SELECT COUNT(*) FROM registration WHERE Enrollment_NO = %s"
        cursor.execute(query, (enrollment_no,))
        result = cursor.fetchone()

        if result[0] == 0:
            return jsonify({"error": "Enrollment number not found"}), 404

        # Step 5: Get subject based on time from the subject table
        subject_query = """
            SELECT subject_code 
            FROM subject 
            WHERE %s BETWEEN start_time AND end_time
        """
        cursor.execute(subject_query, (current_time,))
        subject_result = cursor.fetchone()

        if not subject_result:
            return jsonify({"error": "No subject scheduled at this time"}), 404

        subject_code = subject_result[0]

        # Step 6: Mark attendance
        insert_query = """
            INSERT INTO attendance (Enrollment_NO, attendance_date, attendance_time, subject_code, status) 
            VALUES (%s, %s, %s, %s, 'P')
        """
        cursor.execute(insert_query, (enrollment_no, current_date, current_time, subject_code))
        connection.commit()

        return jsonify({"message": "Attendance marked successfully"}), 200

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        enrollment_no = request.form['Enrollment']
        phone_no = request.form['Phone']
        email = request.form['email']
        password = request.form['password']
        address = request.form['address']

        # Database connection
        try:
            connection = connect_to_db()
            cursor = connection.cursor()
            
            # Insert query
            insert_query = """
                INSERT INTO registration (Name, Enrollment_NO, Phone_NO, Email, Password, Address)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            data = (name, enrollment_no, phone_no, email, password, address)

            cursor.execute(insert_query, data)  # Execute query
            connection.commit()                # Commit transaction

            print("Registration successful!", "success")
            return redirect(url_for('profile'))
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            flash("An error occurred during registration. Please try again.", "error")
        finally:
            if 'cursor' in locals():  # Check if cursor exists
                cursor.close()
            if 'connection' in locals():  # Check if connection exists
                connection.close()

    return render_template('register.html')



@app.route('/profile')
def profile():
    if 'user' not  in session:
        return redirect(url_for('login'))
    user = session['user']
    print(session['name'])
    data=alldata()
    for i in data:
        print(i)
    return render_template('profile.html', records=data)
  
@app.route('/teacher', methods=['GET', 'POST'])
def teacher():
    if 'username' not in session or session.get('role') != 'teacher':
        return redirect(url_for('login'))
    connection = connect_to_db()
    cursor = connection.cursor()
    query = "SELECT * FROM teacher WHERE username = %s AND password = %s"
    # print(session[0],type(session))
    # cursor.execute(query, (enrollment_no, password))
    # user = cursor.fetchone()
    # print(type(user))
    
    # return render_template('teacher.html',tech=name)
    return None

@app.route('/student', methods=['GET', 'POST'])
def student():
    # if 'enrollment_no' not in session or session.get('role') != 'student':
    #     return redirect(url_for('login'))
    # enrollment=session['enrollment_no'] 
    # fetch_student_by_enrollment()
    # print(enrollment)
    # student_details=fetch_student_by_enrollment(enrollment)
    return render_template('student.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
