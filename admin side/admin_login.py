from flask import Flask, render_template, request, redirect
import subprocess
import mysql.connector
import app
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired
from flask_bootstrap import Bootstrap

app = Flask(__name__)
Bootstrap(app)
# Database configuration
# Replace with your actual database connection details

mysql_password = "Qwerty12"
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password=mysql_password,
    database="aptitude_test"
)
cursor = db.cursor()


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the username and password match the users table
        cursor = db.cursor()
        query = "SELECT * FROM users WHERE username = %s AND password = %s"
        values = (username, password)
        cursor.execute(query, values)
        user = cursor.fetchone()

        if user:
            # Execute app.py
            subprocess.run(["python", "app.py"])
            return "App executed successfully!"
        else:
            return "Invalid username or password"

    return render_template('login.html')

if __name__ == '__main__':
    app.run()