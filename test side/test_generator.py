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
import base64
import os
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

mysql_password = "Qwerty12"

app = Flask(__name__)
app.secret_key = 'fbwBEJKWFBKWEFEW'
app.secret_key = secrets.token_bytes(32)

SECTIONS = ['english', 'mathematics', 'physics', 'reasoning']


db = mysql.connector.connect(
    host="localhost",
    user="root",
    password=mysql_password,
    database="aptitude_test"
)
cursor = db.cursor()


def get_random_questions(section, num_questions):
    sql = """
        SELECT q.question_id, q.question_text, qi.image_data
        FROM questions q
        LEFT JOIN question_images qi ON q.question_id = qi.question_id
        WHERE q.section = %s AND q.passage_id IS NULL
        ORDER BY RAND()
        LIMIT %s;
    """
    values = (section, num_questions)
    cursor.execute(sql, values)
    results = cursor.fetchall()

    questions = []
    # questions_to_send =[]
    current_question = None

    for result in results:
        question_id, question_text, question_image_data = result
        # print(f'{question_text[:20]} -> {question_id} {question_image_data} ')

        if current_question is None or question_id != current_question["id"]:
            current_question = {
                "id": question_id,
                "text": question_text,
                "question_image_data": question_image_data,
                "options": []
            }
            questions.append(current_question)


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

def get_questions_by_subsection(section, subsection, num_questions=5):
    # Get individual questions for the given section and subsection
    sql = """
        SELECT q.question_id, q.question_text, qi.image_data, p.passage_id, p.passage_text,
               o.option_id, o.option_text, o.is_correct, oi.image_data
        FROM questions q
        LEFT JOIN question_images qi ON q.question_id = qi.question_id
        LEFT JOIN options o ON q.question_id = o.question_id
        LEFT JOIN option_images oi ON o.option_id = oi.option_id
        LEFT JOIN passages p ON q.passage_id = p.passage_id
        WHERE q.section = %s AND q.subsection = %s
        ORDER BY q.question_id, o.option_id
        LIMIT %s
    """
    values = (section, subsection, num_questions)
    cursor.execute(sql, values)
    results = cursor.fetchall()

    questions = []
    current_passage = None
    current_question = None

    for result in results:
        question_id, question_text, question_image_data, passage_id, passage_text, option_id, option_text, is_correct, option_image_data = result

        if passage_id is not None and (current_passage is None or current_passage["id"] != passage_id):
            current_passage = {
                "id": passage_id,
                "text": passage_text,
                "questions": []
            }
            questions.append(current_passage)

        if question_id is not None and (current_question is None or current_question["id"] != question_id):
            current_question = {
                "id": question_id,
                "text": question_text,
                "question_image_data": question_image_data,
                "options": []
            }
            current_passage["questions"].append(current_question)

        if option_id is not None:
            current_question["options"].append({
                "id": option_id,
                "text": option_text,
                "is_correct": is_correct,
                "option_image_data": option_image_data
            })

    return questions

def get_passages_with_questions():
    sql = """
        SELECT p.passage_id, p.passage_text
        FROM passages p
        JOIN questions q ON p.passage_id = q.passage_id
        WHERE q.section = 'English'
        GROUP BY p.passage_id
    """
    cursor.execute(sql)
    passages = cursor.fetchall()

    passages_with_questions = []

    for passage in passages:
        passage_id, passage_text = passage

        sql = """
            SELECT q.question_id, q.question_text, 
                   o.option_id, o.option_text, o.is_correct
            FROM questions q
            LEFT JOIN options o ON q.question_id = o.question_id
            WHERE q.passage_id = %s
            ORDER BY q.question_id, o.option_id
        """
        values = (passage_id,)
        cursor.execute(sql, values)
        results = cursor.fetchall()

        questions = []
        current_question = None

        for result in results:
            question_id, question_text, option_id, option_text, is_correct = result

            if current_question is None or question_id != current_question["id"]:
                current_question = {
                    "id": question_id,
                    "text": question_text,
                    "options": []
                }
                questions.append(current_question)

            if option_id is not None:
                current_question["options"].append({
                    "id": option_id,
                    "text": option_text,
                    "is_correct": is_correct
                })

        passages_with_questions.append({
            "passage_id": passage_id,
            "passage_text": passage_text,
            "questions": questions
        })

    return passages_with_questions


def generate_test(num_questions):
    sections_with_question_ids = {}
    sections = get_sections()

    for section in sections:
        if section == 'english':
            passages_with_question_ids = get_passages_with_questions_by_subsections()
            sections_with_question_ids[section] = passages_with_question_ids
        else:
            section_questions = get_random_questions(section, num_questions)
            sections_with_question_ids[section] = [question['id'] for question in section_questions]

    return sections_with_question_ids

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
            consume_results=True 
        )
        cursor = db.cursor(prepared=True)  

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
    result_lines.append("Result:\n")
    for section, score in section_scores.items():
        if section is not None:  # Check if subsection is not None
            correct = score["correct"]
            total = score["total"]
            result_line = f"{section.capitalize()}: {correct}/{total} = {100*correct/total}%\n"
            result_lines.append(result_line)
            result_line = ""
            if correct / total < 0.35:
                result_line = f"Need too much improvement in {section}\n\n"
            elif correct / total < 0.6:
                result_line = f"Need improvement in {section}\n\n"
            elif correct / total > 0.85:
                result_line = f"{section.capitallize()} is a strength of yours\n\n"
            result_lines.append(result_line)

            total_score += correct
            total_questions += total


    result_lines.append(f"\nTotal Score: {total_score}/{total_questions} = {100*total_score/total_questions}%\n\n\n")

    result_lines.append(f"\n A minimum of 20% in each section and a minimum of 33% overall is required for the qualification of the test.")

    result_message = "\n".join(result_lines)

    sender_email = "your_mailtrap_username@example.com"
    smtp_server = "sandbox.smtp.mailtrap.io"
    smtp_port = 2525
    smtp_username = "c2c484850f91df"
    smtp_password = "b93a5be2b8c831"
    admin_email = "admin@example.com"

    # Create the email message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = admin_email
    msg['Subject'] = "Aptitude Test Result"

    # Attach the result message as plain text
    msg.attach(MIMEText(result_message, 'plain'))

    # Attach the image from the static folder
    image_path = os.path.join('static', 'fulllogo_nobuffer.jpg')  # Update with your image file path
    with open(image_path, 'rb') as img_file:
        img = MIMEImage(img_file.read())
        img.add_header('Content-ID', '<image1>')
        img.add_header('Content-Disposition', 'inline', filename='your_image.jpg')
        msg.attach(img)

    # Add HTML part with the image reference
    html = f"""
    <html>
    <body style="text-align: center;">
        <img src="cid:image1" style="width: 50%; height: auto;"><br>
        <h2>Student Name: {receiver_name}</h2>
        <h3>Email: {receiver_email}</h3>
        <pre style="text-align: left;">{result_message}</pre>
    </body>
    </html>
    """
    msg.attach(MIMEText(html, 'html'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.login(smtp_username, smtp_password)
        server.sendmail(sender_email, admin_email, msg.as_string())
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
def send_email(receiver_email,receiver_name, password):
    sender_email = "info@eifta.in"
    smtp_server = "sandbox.smtp.mailtrap.io"
    smtp_port = 2525
    smtp_username = "c2c484850f91df"
    smtp_password = "b93a5be2b8c831"

    message = f"Subject: One-Time Login and Password\n\n Dear {receiver_name},\n Your login details for EIFTA aptitude test are \n\nLogin: {receiver_email}\nPassword: {password}"

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.login(smtp_username, smtp_password)
        server.sendmail(sender_email, receiver_email, message)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        server.quit()


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
            else:
                section_scores[section]["correct"] += 0


def get_passages_with_questions_by_subsections():
    # Get all subsections for the 'English' section
    sql = "SELECT DISTINCT subsection FROM questions WHERE section = 'English'"
    cursor.execute(sql)
    subsections = [row[0] for row in cursor.fetchall()]

    passages_with_question_ids = []

    for subsection in subsections:
       
        sql = """
            SELECT p.passage_id
            FROM passages p
            JOIN questions q ON p.passage_id = q.passage_id
            WHERE q.section = 'English' AND q.subsection = %s
            GROUP BY p.passage_id
            ORDER BY RAND()
            LIMIT 1
        """
        values = (subsection,)
        cursor.execute(sql, values)
        passage = cursor.fetchone()

        if passage:
            passage_id = passage[0]

       
            sql = """
                SELECT question_id
                FROM questions
                WHERE passage_id = %s
                LIMIT 5
            """
            values = (passage_id,)
            cursor.execute(sql, values)
            question_ids = [row[0] for row in cursor.fetchall()]

            passages_with_question_ids.append({
                "passage_id": passage_id,
                "question_ids": question_ids
            })

    return passages_with_question_ids

def initialize_section_scores():
    for section in SECTIONS:
        section_scores[section]['total'] = 25


def get_questions_by_ids(question_ids):
    questions = []

    for question_id in question_ids:
    
        sql = "SELECT question_id, question_text FROM questions WHERE question_id = %s"
        values = (question_id,)
        cursor.execute(sql, values)
        result = cursor.fetchone()

        if result:
            question = {
                'id': result[0],
                'text': result[1],
                'options': []
            }

            
            sql = "SELECT option_id, option_text, is_correct FROM options WHERE question_id = %s"
            values = (question_id,)
            cursor.execute(sql, values)
            results = cursor.fetchall()

            for result in results:
                option = {
                    'id': result[0],
                    'text': result[1],
                    'is_correct': result[2]
                }
                question['options'].append(option)

            questions.append(question)

    return questions

def get_passage_text(passage_id):
    sql = "SELECT passage_text FROM passages WHERE passage_id = %s"
    values = (passage_id,)
    cursor.execute(sql, values)
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        return None

@app.route('/start_timer')
def start_timer():
    if 'start_timer' not in session:
        session['start_timer'] = datetime.now(pytz.utc)
        session['duration'] = 5400  
        return 'Timer started'
    return 'Timer already started'

@app.route('/update_tab_switch_counter', methods=['POST'])
def update_tab_switch_counter():
    if request.method == 'POST':
        data = request.get_json()
        tab_switch_counter = data.get('tab_switch_counter', 0)
        session['tab_switch_counter'] = tab_switch_counter
        return 'Tab switch counter updated'
    return 'Invalid request method'

@app.route('/time_remaining')
def time_remaining():
    if 'start_timer' in session:
        start_time = session.get('start_timer')
        duration = session.get('duration')
        elapsed = (datetime.now(pytz.utc) - start_time).total_seconds()
        remaining = max(duration - elapsed, 0)

        tab_switch_counter = session.get('tab_switch_counter', 0)
        penalty_time = 5 * max((tab_switch_counter - 1),0) * 60
        remaining = max(remaining - penalty_time, 0)
        

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
            test_question_ids = generate_test(num_questions=25)  
            session['test_question_ids'] = test_question_ids
            session['is_answer_submitted'] = False
            return redirect(url_for('test'))
        else:
            return render_template('index.html', error='Invalid credentials')

    return render_template('index.html')

section_scores = defaultdict(lambda:{"correct": 0, "total": 25})


@app.route('/test', methods=['GET', 'POST'])
def test():
    if request.method == 'POST':
        user_answers = request.form
        session['user_answers'] = user_answers
        initialize_section_scores()
        evaluate_user_answers(user_answers)
        calculate_score_and_send_email(section_scores)
        print()
        return redirect(url_for('thank_you'))
    session['is_answer_submitted'] = False
    if 'login' not in session or 'password' not in session:
        return redirect(url_for('index'))

    mark_test_started(session['login'], session['password'])

    test_question_ids = session.get('test_question_ids')
    # print(test_question_ids)
    test_questions = {}

    for section, data in test_question_ids.items():
        if section == 'english':
            passages_with_questions = []
            for entry in data:
                passage_id = entry['passage_id']
                question_ids = entry['question_ids']

                passage_text = get_passage_text(passage_id)
                questions = get_questions_by_ids(question_ids)

                passage_with_questions = {
                    'passage_id': passage_id,
                    'passage_text': passage_text,
                    'questions': questions
                }
                passages_with_questions.append(passage_with_questions)
            
     

            test_questions[section] = passages_with_questions
     
        else:
            section_questions = get_questions_by_ids(data)
            test_questions[section] = section_questions
    time_remaining = 5400
   

    if request.method == 'GET':
    

        time_remaining = session.get('time_remaining', 90 * 60)

        if 'start_time' not in session:
            session['start_time'] = time.time()
        
        if 'tab_switch_counter' not in session:
            session['tab_switch_counter'] = 0
        tabSwitchCounter = session['tab_switch_counter']

    elapsed_time = time.time() - session['start_time']
    time_remaining = time_remaining - elapsed_time

    tab_switch_counter = session.get('tab_switch_counter', 0)
    penalty_time = 5 * max((tab_switch_counter - 1),0) * 60
    time_remaining -= penalty_time





    session['time_remaining'] = time_remaining

    return render_template('test.html', test_questions=test_questions, time_remaining=time_remaining)

@app.route('/thank_you')
def thank_you():
    session.clear()
    return render_template('thank_you.html')

@app.teardown_appcontext
def close_db_connection(exception):
    db = getattr(flask.g, '_database', None)
    if db is not None:
        db.close()


receiver_email = "hello7@example.com" # take it from payments page.
receiver_name  = "Student" # take it from payments page.
if __name__ == '__main__':
    password = generate_password()

    store_credentials(receiver_email, password)
    send_email(receiver_email,receiver_name, password)
    # print(password)

    app.run()

