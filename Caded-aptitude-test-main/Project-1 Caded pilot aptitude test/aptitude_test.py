import mysql.connector

# Connect to MySQL database
db = mysql.connector.connect(
    host="your_host",
    user="your_username",
    password="your_password",
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

# Functions to interact with the database
def add_question(question_text, section, subsection):
    sql = "INSERT INTO questions (question_text, section, subsection) VALUES (%s, %s, %s)"
    values = (question_text, section, subsection)
    cursor.execute(sql, values)
    db.commit()
    return cursor.lastrowid

def add_option(question_id, option_text, is_correct):
    sql = "INSERT INTO options (question_id, option_text, is_correct) VALUES (%s, %s, %s)"
    values = (question_id, option_text, is_correct)
    cursor.execute(sql, values)
    db.commit()

def get_questions(section):
    sql = "SELECT * FROM questions WHERE section = %s"
    values = (section,)
    cursor.execute(sql, values)
    return cursor.fetchall()

# Admin interface functions (similar to the previous example)
def admin_menu():
    while True:
        print("Admin Menu:")
        print("1. Add Question")
        print("2. List Questions")
        print("3. Exit")
        choice = input("Enter your choice: ")

        if choice == "1":
            add_question_menu()
        elif choice == "2":
            list_questions_menu()
        elif choice == "3":
            break
        else:
            print("Invalid choice. Please try again.")

def add_question_menu():
    question_text = input("Enter the question text: ")
    section = input("Enter the section (e.g., Basic Mathematics, Basic Physics): ")
    subsection = input("Enter the subsection (e.g., Algebra, Mechanics): ")

    question_id = add_question(question_text, section, subsection)

    num_options = int(input("Enter the number of options: "))
    for i in range(num_options):
        option_text = input(f"Enter option {i+1}: ")
        is_correct = input(f"Is option {i+1} correct? (y/n): ")
        is_correct = 1 if is_correct.lower() == "y" else 0
        add_option(question_id, option_text, is_correct)

    print("Question added successfully.")


def list_questions_menu():
    section = input("Enter the section to list questions: ")
    questions = get_questions(section)

    if not questions:
        print("No questions found for the specified section.")
    else:
        for question in questions:
            question_id, question_text, section, subsection = question
            print(f"Question ID: {question_id}")
            print(f"Question Text: {question_text}")
            print(f"Section: {section}")
            print(f"Subsection: {subsection}")
            print()

if __name__ == "__main__":
    admin_menu()