import mysql.connector
import random
from collections import defaultdict
import flask
from flask import Flask, render_template, request, redirect, url_for, g
from flask import session
import secrets
import json
from flask_mail import Mail, Message
from flask import jsonify
import mailtrap as mt
from mailtrap import Mail, Address, MailtrapClient
import smtplib
import string
import time
from datetime import datetime, timedelta
import pytz

mysql_password = "Qwerty12"

app = Flask(__name__)
app.secret_key = 'fbwBEJKWFBKWEFEW'
app.secret_key = secrets.token_bytes(32)

# Connect to MySQL database
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password=mysql_password,
    database="aptitude_test"
)
cursor = db.cursor()

def get_random_questions(section, num_questions):
    subsections = get_subsections(section)
    questions = []
    remaining_questions = num_questions

    for subsection in subsections:
        subsection_questions = get_questions_by_subsection(section, subsection)
        num_subsection_questions = min(len(subsection_questions), int(remaining_questions / (len(subsections) - len(questions))))
        questions.extend(random.sample(subsection_questions, num_subsection_questions))
        remaining_questions -= num_subsection_questions

    random.shuffle(questions)
    return questions

def get_sections():
    sql = "SELECT DISTINCT section FROM questions"
    cursor.execute(sql)
    return [row[0] for row in cursor.fetchall()]

def get_subsections(section):
    sql = "SELECT DISTINCT subsection FROM questions WHERE section = %s"
    values = (section,)
    cursor.execute(sql, values)
    return [row[0] for row in cursor.fetchall()]

def get_questions_by_subsection(section, subsection):
    sql = """
        SELECT q.question_id, q.question_text, q.section, q.subsection, qi.image_data
        FROM questions q
        LEFT JOIN question_images qi ON q.question_id = qi.question_id
        WHERE q.section = %s AND q.subsection = %s
    """
    values = (section, subsection)
    cursor.execute(sql, values)
    questions = cursor.fetchall()

    options_dict = defaultdict(list)
    for question in questions:
        question_id, question_text, section, subsection, question_image_data = question
        options_dict[question_id] = {
            "id": question_id,
            "text": question_text,
            "section": section,
            "subsection": subsection,
            "question_image_data": question_image_data,
            "options": []
        }

    sql = """
        SELECT o.question_id, o.option_id, o.option_text, o.is_correct, oi.image_data
        FROM options o
        LEFT JOIN option_images oi ON o.option_id = oi.option_id
        JOIN questions q ON o.question_id = q.question_id
        WHERE q.section = %s AND q.subsection = %s
    """
    values = (section, subsection)
    cursor.execute(sql, values)
    options = cursor.fetchall()

    for option in options:
        question_id, option_id, option_text, is_correct, option_image_data = option
        options_dict[question_id]["options"].append({
            "id": option_id,
            "text": option_text,
            "is_correct": is_correct,
            "option_image_data": option_image_data
        })

    return list(options_dict.values())

def generate_test(num_questions):
    sections_with_questions = {}
    sections = get_sections()

    for section in sections:
        sections_with_questions[section] = get_random_questions(section, num_questions)

    return sections_with_questions

def get_section_for_question(question_id):
    sql = "SELECT section FROM questions WHERE question_id = %s"
    values = (question_id,)

    try:
        cursor.execute(sql, values)
        result = cursor.fetchone()
        if result:
            section = result[0]
            if section is None:
                print(f"Warning: Question {question_id} has a NULL section.")
            return section
        else:
            print(f"Warning: No section found for question {question_id}.")
            return None
    except mysql.connector.Error as error:
        print(f"Error fetching section: {error}")
        return None

def get_subsection_for_question(question_id):
    sql = "SELECT subsection FROM questions WHERE question_id = %s"
    values = (question_id,)

    try:
        cursor.execute(sql, values)
        result = cursor.fetchone()
        if result:
            subsection = result[0]
            if subsection is None:
                print(f"Warning: Question {question_id} has a NULL subsection.")
            return subsection
        else:
            print(f"Warning: No subsection found for question {question_id}.")
            return None
    except mysql.connector.Error as error:
        print(f"Error fetching subsection: {error}")
        return None

def get_correct_option(question_id):
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password=mysql_password,
            database="aptitude_test",
            consume_results=True  # Added this line
        )
        cursor = db.cursor(prepared=True)  # Added prepared=True

        sql = "SELECT option_id FROM options WHERE question_id = %s AND is_correct = 1"
        values = (question_id,)

        cursor.execute(sql, values)
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return None
    except mysql.connector.Error as error:
        print(f"Error fetching correct option: {error}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'db' in locals() and db.is_connected():
            db.close()


    
def calculate_score_and_send_email(section_scores):
    total_score = 0
    total_questions = 0
    result_lines = []
    result_lines.append("Result:")
    for section, score in section_scores.items():
        if section is not None:  # Check if subsection is not None
            correct = score["correct"]
            total = score["total"]
            result_line = f"{section}: {correct}/{total}"
            if(total!=0):
                result_lines.append(result_line)
            total_score += correct
            total_questions += total

    result_lines.append(f"\nTotal Score: {total_score}/{total_questions}\n\n\n")
    

    for section, score in section_scores.items():
        if section is not None:  # Check if subsection is not None
            correct = score["correct"]
            total = score["total"]
            if(total!=0):
                result_line=""
                if(correct/total<0.35):
                    result_line = f"need too much improvement in this {section}\n"
                elif(correct/total<0.6):
                    result_line=f"need improvement in this {section}\n"
                elif(correct/total>0.85):
                    result_line=f"{section} is a strength of yours\n"
                result_lines.append(result_line)

    result_message = "\n".join(result_lines)



    sender_email = "your_mailtrap_username@example.com"
    smtp_server = "sandbox.smtp.mailtrap.io"
    smtp_port = 2525
    smtp_username = "c3b9d6f98d9e68"
    smtp_password = "e3be98d7001d2b"

    # Admin email address
    admin_email = "admin@example.com"

    message = f"Subject: Aptitude Test Result\n\n{result_message}"

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.login(smtp_username, smtp_password)
        server.sendmail(sender_email, admin_email, message)
        print("Result Email sent successfully to admin!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        server.quit()

def generate_password(length=10):
    characters = string.ascii_letters + string.digits
    password = ''.join(random.choice(characters) for i in range(length))
    return password

# Function to send an email
def send_email(receiver_email, password):
    sender_email = "admin@example.com"
    smtp_server = "sandbox.smtp.mailtrap.io"
    smtp_port = 2525
    smtp_username = "c3b9d6f98d9e68"
    smtp_password = "e3be98d7001d2b"

    message = f"Subject: One-Time Login and Password\n\nLogin: {receiver_email}\nPassword: {password}"

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.login(smtp_username, smtp_password)
        server.sendmail(sender_email, receiver_email, message)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        server.quit()
# Function to store the one-time login and password in a MySQL database
def store_credentials(login, password):
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password=mysql_password,
            database="aptitude_test"
        )
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                id INT AUTO_INCREMENT PRIMARY KEY,
                login VARCHAR(255) ,
                password VARCHAR(255),
                used BOOLEAN DEFAULT FALSE,
                test_started BOOLEAN DEFAULT FALSE
            )
        """)
        cursor.execute("INSERT INTO credentials (login, password) VALUES (%s, %s)", (login, password))
        db.commit()
    except mysql.connector.Error as error:
        print(f"Error: {error}")
    finally:
        if 'db' in locals() and db.is_connected():
            cursor.close()
            db.close()

# Function to validate the one-time login and password
def validate_credentials(login, password):
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password=mysql_password,
            database="aptitude_test"
        )
        cursor = db.cursor()
        cursor.execute("SELECT * FROM credentials WHERE login = %s AND password = %s AND used = 0 AND test_started = 0", (login, password))
        result = cursor.fetchone()
        if result:
            return True
        else:
            return False
    except mysql.connector.Error as error:
        print(f"Error: {error}")
    finally:
        if 'db' in locals() and db.is_connected():
            cursor.close()
            db.close()

# Function to mark credentials as used after starting the test
def mark_test_started(login, password):
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password=mysql_password,
            database="aptitude_test"
        )
        cursor = db.cursor()
        cursor.execute("UPDATE credentials SET used = 1, test_started = 1 WHERE login = %s AND password = %s", (login, password))
        db.commit()
    except mysql.connector.Error as error:
        print(f"Error: {error}")
    finally:
        if 'db' in locals() and db.is_connected():
            cursor.close()
            db.close()

def evaluate_user_answers(user_answers):
    for question_id, answer_id in user_answers.items():
        if question_id.startswith('question'):
            correct_option = get_correct_option(int(question_id.replace('question', '')))
            section = get_section_for_question(int(question_id.replace('question', '')))

            if int(answer_id) == correct_option:
                section_scores[section]["correct"] += 1

@app.route('/start_timer')
def start_timer():
    if 'start_timer' not in session:
        session['start_timer'] = datetime.now(pytz.utc)
        session['duration'] = 5400  # 90 minutes in seconds
        return 'Timer started'
    return 'Timer already started'

@app.route('/time_remaining')
def time_remaining():
        if 'start_timer' in session: 
            start_time = session.get('start_timer')
            duration = session.get('duration')
            elapsed = (datetime.now(pytz.utc) - start_time).total_seconds()
            remaining = max(duration - elapsed, 0)
            return str(int(remaining))
        else:
            return '5400'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':

        login = request.form['email']
        password = request.form['password']
        if validate_credentials(login, password):
            session['login'] = login
            session['password'] = password
            test_questions = generate_test(num_questions=20)  # Fixed number of questions for all sections
            session['test_questions'] = test_questions  # Store in session
            return redirect(url_for('test'))
        else:
            return render_template('index.html', error='Invalid credentials')

    return render_template('index.html')

section_scores = defaultdict(lambda: {"correct": 0, "total": 20})

@app.route('/test', methods=['GET', 'POST'])
def test():
    if 'login' not in session or 'password' not in session:
        return redirect(url_for('index'))

    mark_test_started(session['login'], session['password'])

    test_questions = session.get('test_questions')

    time_remaining = 5400

    if request.method == 'GET':
        # Get the remaining time from the session or set it to the initial value
        time_remaining = session.get('time_remaining', 90 * 60)

        # Store the start time in the session when the test page is loaded
        if 'start_time' not in session:
            session['start_time'] = time.time()

    elapsed_time = time.time() - session['start_time']
    time_remaining = time_remaining - elapsed_time

    if time_remaining <= 0:
        # Time limit exceeded, evaluate user answers and redirect to the thank you page
        user_answers = session.get('user_answers', {})
        evaluate_user_answers(user_answers)
        section_scores_filtered = {k: v for k, v in section_scores.items() if v is not None}
        calculate_score_and_send_email(section_scores_filtered)
        return redirect(url_for('thank_you'))

    if request.method == 'POST':
        user_answers = request.form
        session['user_answers'] = user_answers

        # Evaluate user answers and calculate subsection scores
        evaluate_user_answers(user_answers)
        # Filter out any None values from the subsection_scores dictionary
        section_scores_filtered = {k: v for k, v in section_scores.items() if v is not None}
        calculate_score_and_send_email(section_scores_filtered)  # No need to pass receiver_email
        return redirect(url_for('thank_you'))

    # Store the remaining time in the session
    session['time_remaining'] = time_remaining

    return render_template('test.html', test_questions=test_questions, time_remaining=time_remaining)

@app.route('/Thank you')
def thank_you():
    session.clear()
    return render_template('thank_you.html')

@app.teardown_appcontext
def close_db_connection(exception):
    db = getattr(flask.g, '_database', None)
    if db is not None:
        db.close()

if __name__ == '__main__':
    receiver_email = "hello7@example.com"
    password = generate_password()
    print(f'password: {password}')

    store_credentials(receiver_email, password)
    # send_email(receiver_email, password)

    app.run()