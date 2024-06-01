import mysql.connector
import random
from collections import defaultdict
import os
from pathlib import Path


# Connect to MySQL database
mysql_password = "Qwerty12"
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password=mysql_password,
    database="aptitude_test"
)
cursor = db.cursor()

# Create tables if they don't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS passages (
    passage_id INT AUTO_INCREMENT PRIMARY KEY,
    passage_text TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS questions (
    question_id INT AUTO_INCREMENT PRIMARY KEY,
    question_text TEXT NOT NULL,
    section VARCHAR(255) NOT NULL,
    subsection VARCHAR(255) NOT NULL,
    passage_id INT NULL,
    FOREIGN KEY (passage_id) REFERENCES passages(passage_id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS options (
    option_id INT AUTO_INCREMENT PRIMARY KEY,
    question_id INT NOT NULL,
    option_text TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL,
    FOREIGN KEY (question_id) REFERENCES questions(question_id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS question_images (
    image_id INT AUTO_INCREMENT PRIMARY KEY,
    question_id INT NOT NULL,
    image_data LONGBLOB NOT NULL,
    FOREIGN KEY (question_id) REFERENCES questions(question_id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS option_images (
    image_id INT AUTO_INCREMENT PRIMARY KEY,
    option_id INT NOT NULL,
    image_data LONGBLOB NOT NULL,
    FOREIGN KEY (option_id) REFERENCES options(option_id)
)
""")
# Admin interface functions
def add_passage(passage_text):
    sql = "INSERT INTO passages (passage_text) VALUES (%s)"
    values = (passage_text,)
    cursor.execute(sql, values)
    db.commit()
    return cursor.lastrowid

def update_passage(passage_id, new_passage_text):
    sql = "UPDATE passages SET passage_text = %s WHERE passage_id = %s"
    values = (new_passage_text, passage_id)
    cursor.execute(sql, values)
    db.commit()
    print("Passage updated successfully.")

def delete_passage(passage_id):
    # Delete associated questions and their options/images
    sql = "SELECT question_id FROM questions WHERE passage_id = %s"
    values = (passage_id,)
    cursor.execute(sql, values)
    question_ids = [row[0] for row in cursor.fetchall()]

    for question_id in question_ids:
        delete_question(question_id)

    # Delete the passage
    sql = "DELETE FROM passages WHERE passage_id = %s"
    cursor.execute(sql, values)

    db.commit()
    print("Passage deleted successfully.")

def get_all_questions():
    # Select all questions from the questions table
    sql = "SELECT question_id, question_text, section, subsection FROM questions"
    cursor.execute(sql)

    # Fetch all the rows
    questions = cursor.fetchall()
    questions_list = []
    for question in questions:
        question_dict = {
            'id': question[0],
            'text': question[1],
            'section': question[2],
            'subsection': question[3]
        }
        questions_list.append(question_dict)

    return questions_list
def add_question(question_text, section, subsection, passage_id=None, image_data=None):
    sql = "INSERT INTO questions (question_text, section, subsection, passage_id) VALUES (%s, %s, %s, %s)"
    values = (question_text, section, subsection, passage_id)
    cursor.execute(sql, values)
    db.commit()
    question_id = cursor.lastrowid

    if image_data:
        sql = "INSERT INTO question_images (question_id, image_data) VALUES (%s, %s)"
        values = (question_id, image_data)
        cursor.execute(sql, values)
        db.commit()

    return question_id


def update_question(question_id, question_text, section, subsection):
    sql = "UPDATE questions SET question_text = %s, section = %s, subsection = %s WHERE question_id = %s"
    values = (question_text, section, subsection, question_id)
    cursor.execute(sql, values)
    db.commit()

    # add_or_update_question_image(question_id)

def add_or_update_question_image(question_id):
    has_image = input("Does this question have an image? (y/n): ").lower() == "y"
    if has_image:
        image_file_path = input("Enter the path to the image file (without quotes): ")
        image_file = Path(image_file_path)
        with image_file.open("rb") as f:
            image_data = f.read()
        sql = "INSERT INTO question_images (question_id, image_data) VALUES (%s, %s) ON DUPLICATE KEY UPDATE image_data = VALUES(image_data)"
        values = (question_id, image_data)
        cursor.execute(sql, values)
        db.commit()
    else:
        sql = "DELETE FROM question_images WHERE question_id = %s"
        values = (question_id,)
        cursor.execute(sql, values)
        db.commit()

def delete_question(question_id):
    # Delete associated options and their images
    sql = "SELECT option_id FROM options WHERE question_id = %s"
    values = (question_id,)
    cursor.execute(sql, values)
    option_ids = [row[0] for row in cursor.fetchall()]

    for option_id in option_ids:
        # Delete associated option image
        sql = "DELETE FROM option_images WHERE option_id = %s"
        cursor.execute(sql, (option_id,))

    # Delete associated options
    sql = "DELETE FROM options WHERE question_id = %s"
    cursor.execute(sql, values)

    # Delete the question
    sql = "DELETE FROM questions WHERE question_id = %s"
    cursor.execute(sql, values)

    # Delete associated question image
    sql = "DELETE FROM question_images WHERE question_id = %s"
    cursor.execute(sql, values)

    db.commit()

def add_option(question_id, option_text, is_correct, option_image_data=None):
    sql = "INSERT INTO options (question_id, option_text, is_correct) VALUES (%s, %s, %s)"
    values = (question_id, option_text, is_correct)
    cursor.execute(sql, values)
    db.commit()
    option_id = cursor.lastrowid

    if option_image_data:
        sql = "INSERT INTO option_images (option_id, image_data) VALUES (%s, %s)"
        values = (option_id, option_image_data)
        cursor.execute(sql, values)
        db.commit()

def update_option(option_id, option_text, is_correct):
    sql = "UPDATE options SET option_text = %s, is_correct = %s WHERE option_id = %s"
    values = (option_text, is_correct, option_id)
    cursor.execute(sql, values)
    db.commit()

    #add_or_update_option_image(option_id)

def add_or_update_option_image(option_id):
    has_image = input("Does this option have an image? (y/n): ").lower() == "y"
    if has_image:
        image_file_path = input("Enter the path to the option image file (without quotes): ")
        image_file = Path(image_file_path)
        with image_file.open("rb") as f:
            image_data = f.read()
        sql = "INSERT INTO option_images (option_id, image_data) VALUES (%s, %s) ON DUPLICATE KEY UPDATE image_data = VALUES(image_data)"
        values = (option_id, image_data)
        cursor.execute(sql, values)
        db.commit()
    else:
        sql = "DELETE FROM option_images WHERE option_id = %s"
        values = (option_id,)
        cursor.execute(sql, values)
        db.commit()

def delete_option(option_id):
    # Delete the option
    sql = "DELETE FROM options WHERE option_id = %s"
    values = (option_id,)
    cursor.execute(sql, values)

    # Delete associated option image
    sql = "DELETE FROM option_images WHERE option_id = %s"
    cursor.execute(sql, values)

    db.commit()

def list_questions(section=None, subsection=None):
    sql = "SELECT q.question_id, q.question_text, q.section, q.subsection, q.passage_id, o.option_id, o.option_text, o.is_correct FROM questions q LEFT JOIN options o ON q.question_id = o.question_id"
    conditions = []
    values = []

    if section:
        conditions.append("q.section = %s")
        values.append(section)

    if subsection:
        conditions.append("q.subsection = %s")
        values.append(subsection)

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += " ORDER BY q.passage_id"

    cursor.execute(sql, values)
    return cursor.fetchall()

def get_question(question_id):
    # Get the question details
    sql = """
        SELECT q.question_text, q.section, q.subsection, p.passage_text
        FROM questions q
        LEFT JOIN passages p ON q.passage_id = p.passage_id
        WHERE q.question_id = %s
    """
    values = (question_id,)
    cursor.execute(sql, values)
    result = cursor.fetchone()

    if result:
        question_text, section, subsection, passage_text = result
        question = {
            'text': question_text,
            'section': section,
            'subsection': subsection,
            'passage': passage_text if passage_text else None
        }

        # Get the options for the question
        sql = """
            SELECT o.option_text, o.is_correct
            FROM options o
            WHERE o.question_id = %s
        """
        values = (question_id,)
        cursor.execute(sql, values)
        options = cursor.fetchall()

        question['options'] = [{'text': option_text, 'is_correct': is_correct} for option_text, is_correct in options]

        return question
    else:
        print(f"Question with ID {question_id} not found.")
        return None


def admin_menu():
    while True:
        print("Admin Menu:")
        print("1. Add Passage")
        print("2. Update Passage")
        print("3. delete Passage")
        print("4. Add Question")
        print("5. Update Question")
        print("6. Delete Question")
        print("7. Add Option")
        print("8. Update Option")
        print("9. Delete Option")
        print("10. List Questions")
        print("11. Exit")
        print("12. to get a question")
        choice = input("Enter your choice: ")

        if choice == "1":
            add_passage_menu()
        elif choice == "2":
            update_passage_menu()
        elif choice == "3":
            delete_passage_menu()
        elif choice == "4":
            add_question_menu()
        elif choice == "5":
            update_question_menu()
        elif choice == "6":
            delete_question_menu()
        elif choice == "7":
            add_option_menu()
        elif choice == "8":
            update_option_menu()
        elif choice == "9":
            delete_option_menu()
        elif choice == "10":
            list_questions_menu()
        elif choice == "11":
            break
        # elif choice == "12":
        #     get_question_menu()
        else:
            print("Invalid choice. Please try again.")

# Helper functions for the admin menu
def add_passage_menu():
    passage_text = input("Enter the passage text: ")
    passage_id = add_passage(passage_text)
    print(f"Passage added with ID: {passage_id}")

def add_question_menu():
    question_text = input("Enter the question text: ")
    section = input("Enter the section: ")
    subsection = input("Enter the subsection: ")
    passage_id = input("Enter the passage ID (leave blank if not related to a passage): ") or None
    if passage_id is not None:
        passage_id = int(passage_id)
    image_data = None
    has_question_image = input("Does this question have an image? (y/n): ").lower() == "y"
    if has_question_image:
        question_image_file_path = input("Enter the path to the question image file (without quotes): ")
        question_image_file = Path(question_image_file_path)
        with question_image_file.open("rb") as f:
            image_data = f.read()
    question_id = add_question(question_text, section, subsection, passage_id, image_data)
    num_options = int(input("Enter the number of options: "))
    for i in range(num_options):
        option_text = input(f"Enter the option text for option {i + 1}: ")
        is_correct = input(f"Is option {i + 1} correct? (y/n): ").lower() == "y"
        option_image_data = None
        if has_question_image:
            has_option_image = input(f"Does option {i + 1} have an image? (y/n): ").lower() == "y"
            if has_option_image:
                option_image_file_path = input("Enter the path to the option image file (without quotes): ")
                option_image_file = Path(option_image_file_path)
                with option_image_file.open("rb") as f:
                    option_image_data = f.read()
        add_option(question_id, option_text, is_correct, option_image_data)

    print(f"Question added with ID: {question_id}")

def update_question_menu():
    question_id = int(input("Enter the question ID to update: "))
    question_text = input("Enter the new question text: ")
    section = input("Enter the new section: ")
    subsection = input("Enter the new subsection: ")
    update_question(question_id, question_text, section, subsection)
    print("Question updated successfully.")

def delete_question_menu():
    question_id = int(input("Enter the question ID to delete: "))
    delete_question(question_id)
    print("Question deleted successfully.")

# def get_question_menu():
#     question_id = int(input("Enter the question ID to get: "))
#     get_question(question_id)

def add_option_menu():
    question_id = int(input("Enter the question ID: "))
    option_text = input("Enter the option text: ")
    is_correct = input("Is this option correct? (y/n): ").lower() == "y"
    option_image_data = None
    has_option_image = input("Does this option have an image? (y/n): ").lower() == "y"
    if has_option_image:
        option_image_file_path = input("Enter the path to the option image file (without quotes): ")
        option_image_file = Path(option_image_file_path)
        with option_image_file.open("rb") as f:
            option_image_data = f.read()
    add_option(question_id, option_text, is_correct, option_image_data)
    print("Option added successfully.")

def update_option_menu():
    option_id = int(input("Enter the option ID to update: "))
    option_text = input("Enter the new option text: ")
    is_correct = input("Is this option correct? (y/n): ").lower() == "y"
    update_option(option_id, option_text, is_correct)
    print("Option updated successfully.")

def delete_option_menu():
    option_id = int(input("Enter the option ID to delete: "))
    delete_option(option_id)
    print("Option deleted successfully.")

def update_passage_menu():
    passage_id = int(input("Enter the passage ID to update: "))
    new_passage_text = input("Enter the new passage text: ")
    update_passage(passage_id, new_passage_text)

def delete_passage_menu():
    passage_id = int(input("Enter the passage ID to delete: "))
    delete_passage(passage_id)

def list_questions_menu():
    section = input("Enter the section (leave blank for all): ") or None
    subsection = input("Enter the subsection (leave blank for all): ") or None
    questions = list_questions(section, subsection)

    if not questions:
        print("No questions found.")
    else:
        current_passage_id = None
        for question in questions:
            question_id, question_text, section, subsection, passage_id, option_id, option_text, is_correct = question
            if passage_id != current_passage_id:
                if current_passage_id is not None:
                    print()  # Add a blank line for separation
                current_passage_id = passage_id
                if passage_id is not None:
                    sql = "SELECT passage_text FROM passages WHERE passage_id = %s"
                    values = (passage_id,)
                    cursor.execute(sql, values)
                    result = cursor.fetchone()
                    if result:
                        passage_text = result[0]
                        print(f"Passage:\n{passage_text}\n")
                    else:
                        print("Warning: Passage not found for the given passage_id.")

            print(f"Question ID: {question_id}")
            print(f"Question Text: {question_text}")
            print(f"Section: {section}")
            print(f"Subsection: {subsection}")
            if not option_id:
                print("No options found for this question.")
            else:
                print(f"Option ID: {option_id}, Option Text: {option_text}, Is Correct: {is_correct}")
            print()

# admin_menu()