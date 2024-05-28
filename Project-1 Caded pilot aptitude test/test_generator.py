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

app = Flask(__name__)
app.secret_key = 'fbwBEJKWFBKWEFEW'
app.secret_key = secrets.token_bytes(32)

# Connect to MySQL database
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Qwerty12",
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
        subsection_scores[subsection]["total"] += num_subsection_questions
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
        SELECT q.question_id, q.question_text, q.section, q.subsection
        FROM questions q
        WHERE q.section = %s AND q.subsection = %s
    """
    values = (section, subsection)
    cursor.execute(sql, values)
    questions = cursor.fetchall()

    options_dict = defaultdict(list)
    for question in questions:
        question_id, question_text, section, subsection = question
        options_dict[question_id] = {
            "id": question_id,
            "text": question_text,
            "section": section,
            "subsection": subsection,
            "options": []
        }

    sql = """
        SELECT o.question_id, o.option_id, o.option_text, o.is_correct
        FROM options o
        JOIN questions q ON o.question_id = q.question_id
        WHERE q.section = %s AND q.subsection = %s
    """
    values = (section, subsection)
    cursor.execute(sql, values)
    options = cursor.fetchall()

    for option in options:
        question_id, option_id, option_text, is_correct = option
        options_dict[question_id]["options"].append({
            "id": option_id,
            "text": option_text,
            "is_correct": is_correct
        })

    return list(options_dict.values())

def generate_test(num_questions):
    sections_with_questions = {}
    sections = get_sections()

    for section in sections:
        sections_with_questions[section] = get_random_questions(section, num_questions)

    return sections_with_questions

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
            password="Qwerty12",
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

    
def calculate_score_and_send_email(subsection_scores):
    total_score = 0
    total_questions = 0
    result_lines = []
    result_lines.append("Result:")
    for subsection, score in subsection_scores.items():
        if subsection is not None:  # Check if subsection is not None
            correct = score["correct"]
            total = score["total"]
            result_line = f"{subsection}: {correct}/{total}"
            if(total!=0):
                result_lines.append(result_line)
            total_score += correct
            total_questions += total

    result_lines.append(f"\nTotal Score: {total_score}/{total_questions}\n\n\n")
    

    for subsection, score in subsection_scores.items():
        if subsection is not None:  # Check if subsection is not None
            correct = score["correct"]
            total = score["total"]
            if(total!=0):
                result_line=""
                if(correct/total<0.35):
                    result_line = f"need too much improvement in this {subsection}\n"
                elif(correct/total<0.6):
                    result_line=f"need improvement in this {subsection}\n"
                elif(correct/total>0.85):
                    result_line=f"{subsection} is a strength of yours\n"
                result_lines.append(result_line)

    result_message = "\n".join(result_lines)



    sender_email = "your_mailtrap_username@example.com"
    smtp_server = "sandbox.smtp.mailtrap.io"
    smtp_port = 2525
    smtp_username = "0efa8edfff526c"
    smtp_password = "37f3af5defab42"

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
    smtp_username = "0efa8edfff526c"
    smtp_password = "37f3af5defab42"

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
            password="Qwerty12",
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
            password="Qwerty12",
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
            password="Qwerty12",
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


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':

        login = request.form['email']
        password = request.form['password']
        if validate_credentials(login, password):
            session['login'] = login
            session['password'] = password
            test_questions = generate_test(num_questions=2)  # Fixed number of questions for all sections
            session['test_questions'] = test_questions  # Store in session
            return redirect(url_for('test'))
        else:
            return render_template('index.html', error='Invalid credentials')

    return render_template('index.html')

subsection_scores = defaultdict(lambda: {"correct": 0, "total": 0})

@app.route('/test', methods=['GET', 'POST'])
def test():
    if 'login' not in session or 'password' not in session:
        return redirect(url_for('index'))
    
    mark_test_started(session['login'], session['password'])

    test_questions = session.get('test_questions')

    if request.method == 'POST':
        user_answers = request.form
        # Evaluate user answers and calculate subsection scores
        
        for question_id, answer_id in user_answers.items():
            print(question_id,answer_id)
            if question_id.startswith('question'):
                correct_option = get_correct_option(int(question_id.replace('question', '')))
                subsection = get_subsection_for_question(int(question_id.replace('question', '')))
                
                if int(answer_id) == correct_option:
                    subsection_scores[subsection]["correct"] += 1
        
        # Print the subsection_scores dictionary for debugging
        print("Subsection scores:")
        for subsection, score in subsection_scores.items():
            if score['total']!=0:
                print(f"{subsection}: {score['correct']}/{score['total']}")
        
        # Filter out any None values from the subsection_scores dictionary
        subsection_scores_filtered = {k: v for k, v in subsection_scores.items() if v is not None}
        calculate_score_and_send_email(subsection_scores_filtered)  # No need to pass receiver_email
        return redirect(url_for('thank_you'))
    return render_template('test.html', test_questions=test_questions)

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

    store_credentials(receiver_email, password)
    send_email(receiver_email, password)

    app.run()