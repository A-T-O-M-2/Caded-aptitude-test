import mysql.connector
import random
from collections import defaultdict


# Connect to MySQL database
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Qwerty12",
    database="aptitude_test"
)
cursor = db.cursor()

# Create tables if they don't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS questions (
    question_id INT AUTO_INCREMENT PRIMARY KEY,
    question_text TEXT NOT NULL,
    section VARCHAR(255) NOT NULL,
    subsection VARCHAR(255) NOT NULL
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



# Admin interface functions
def add_question(question_text, section, subsection):
    sql = "INSERT INTO questions (question_text, section, subsection) VALUES (%s, %s, %s)"
    values = (question_text, section, subsection)
    cursor.execute(sql, values)
    db.commit()
    return cursor.lastrowid

def update_question(question_id, question_text, section, subsection):
    sql = "UPDATE questions SET question_text = %s, section = %s, subsection = %s WHERE question_id = %s"
    values = (question_text, section, subsection, question_id)
    cursor.execute(sql, values)
    db.commit()

def delete_question(question_id):
    sql = "DELETE FROM questions WHERE question_id = %s"
    values = (question_id,)
    cursor.execute(sql, values)
    db.commit()

def add_option(question_id, option_text, is_correct):
    sql = "INSERT INTO options (question_id, option_text, is_correct) VALUES (%s, %s, %s)"
    values = (question_id, option_text, is_correct)
    cursor.execute(sql, values)
    db.commit()

def update_option(option_id, option_text, is_correct):
    sql = "UPDATE options SET option_text = %s, is_correct = %s WHERE option_id = %s"
    values = (option_text, is_correct, option_id)
    cursor.execute(sql, values)
    db.commit()

def delete_option(option_id):
    sql = "DELETE FROM options WHERE option_id = %s"
    values = (option_id,)
    cursor.execute(sql, values)
    db.commit()

def list_questions(section=None, subsection=None):
    sql = "SELECT q.question_id, q.question_text, q.section, q.subsection, o.option_id, o.option_text, o.is_correct FROM questions q LEFT JOIN options o ON q.question_id = o.question_id"
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

    cursor.execute(sql, values)
    return cursor.fetchall()

def admin_menu():
    while True:
        print("Admin Menu:")
        print("1. Add Question")
        print("2. Update Question")
        print("3. Delete Question")
        print("4. Add Option")
        print("5. Update Option")
        print("6. Delete Option")
        print("7. List Questions")
        print("8. Exit")
        choice = input("Enter your choice: ")

        if choice == "1":
            add_question_menu()
        elif choice == "2":
            update_question_menu()
        elif choice == "3":
            delete_question_menu()
        elif choice == "4":
            add_option_menu()
        elif choice == "5":
            update_option_menu()
        elif choice == "6":
            delete_option_menu()
        elif choice == "7":
            list_questions_menu()
        elif choice == "8":
            break
        else:
            print("Invalid choice. Please try again.")

# Helper functions for the admin menu
def add_question_menu():
    question_text = input("Enter the question text: ")
    section = input("Enter the section: ")
    subsection = input("Enter the subsection: ")
    question_id = add_question(question_text, section, subsection)
    num_options= int(input("Enter number of options: "))
    for i in range(num_options):
        option_text = input("Enter the option text: ")
        is_correct = input("Is this option correct? (y/n): ").lower() == "y"
        add_option(question_id, option_text, is_correct)

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

def add_option_menu():
    question_id = int(input("Enter the question ID: "))
    option_text = input("Enter the option text: ")
    is_correct = input("Is this option correct? (y/n): ").lower() == "y"
    add_option(question_id, option_text, is_correct)
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

def list_questions_menu():
    section = input("Enter the section (leave blank for all): ") or None
    subsection = input("Enter the subsection (leave blank for all): ") or None
    questions = list_questions(section, subsection)

    if not questions:
        print("No questions found.")
    else:
        for question in questions:
            question_id, question_text, section, subsection, option_id, option_text, is_correct = question
            print(f"Question ID: {question_id}")
            print(f"Question Text: {question_text}")
            print(f"Section: {section}")
            print(f"Subsection: {subsection}")
            print(f"Option ID: {option_id}, Option Text: {option_text}, Is Correct: {is_correct}")
            print()

if __name__ == "__main__":
    admin_menu()