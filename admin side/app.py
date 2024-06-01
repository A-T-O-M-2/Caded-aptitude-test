from flask import Flask
import mysql.connector
from flask_wtf.csrf import CSRFProtect
from flask import render_template, request, redirect, url_for, flash
import admin_interface
import os
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField, PasswordField,FieldList,FormField, SelectField
from wtforms.validators import DataRequired
from flask_bootstrap import Bootstrap


app = Flask(__name__)
app.config['SECRET_KEY'] = "ciycttuvuvuy"
csrf = CSRFProtect(app)
Bootstrap(app)
mysql_password = "Qwerty12"
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password=mysql_password,
    database="aptitude_test"
)
cursor = db.cursor()

def get_passage_text(passage_id):
    sql = "SELECT passage_text FROM passages WHERE passage_id = %s"
    values = (passage_id,)
    cursor.execute(sql, values)
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        return None
    
class PassageForm(FlaskForm):
    passage_text = TextAreaField('Passage Text', validators=[DataRequired()])
    submit = SubmitField('Submit')

class OptionForm(FlaskForm):
    option_text = TextAreaField('Option Text', validators=[DataRequired()])
    is_correct = BooleanField('Is Correct?')

class QuestionForm(FlaskForm):
    question_text = TextAreaField('Question Text', validators=[DataRequired()])
    section = SelectField('Section', choices=[('Mathematics', 'Mathematics'), ('physics', 'Physics'), ('english', 'English'), ('reasoning', 'Reasoning')], validators=[DataRequired()])
    subsection = SelectField('Subsection', choices=[])
    passage_id = StringField('Passage ID (leave blank if not related to a passage)')
    options = FieldList(FormField(OptionForm), min_entries=4)
    submit = SubmitField('Submit')


class DeleteQuestionForm(FlaskForm):
    question_id = StringField('Question ID', validators=[DataRequired()])

class UpdateQuestionForm(FlaskForm):
    question_id = StringField('Question ID', validators=[DataRequired()])
    question_text = TextAreaField('Question Text', validators=[DataRequired()])
    section = SelectField('Section', choices=[('mathematics', 'Mathematics'), ('physics', 'Physics'), ('english', 'English'), ('reasoning', 'Reasoning')], validators=[DataRequired()])
    subsection = SelectField('Subsection', choices=[], validators=[DataRequired()])
    submit = SubmitField('Update')

class AddOptionForm(FlaskForm):
    question_id = StringField('Question ID', validators=[DataRequired()])
    option_text = TextAreaField('Option Text', validators=[DataRequired()])
    is_correct = BooleanField('Is Correct?')
    submit = SubmitField('Add Option')

class DeleteOptionForm(FlaskForm):
    option_id = StringField('Option ID', validators=[DataRequired()])
    submit = SubmitField('Delete Option')

class UpdateOptionForm(FlaskForm):
    option_text = TextAreaField('Option Text', validators=[DataRequired()])
    is_correct = BooleanField('Is Correct?')
    option_id = StringField('Option ID', validators=[DataRequired()])
    submit = SubmitField('Update Option')

class DeletePassageForm(FlaskForm):
    passage_id = StringField('Passage ID', validators=[DataRequired()])
    submit = SubmitField('Delete Passage')

class UpdatePassageForm(FlaskForm):
    passage_id = StringField('Passage ID', validators=[DataRequired()])
    passage_text = TextAreaField('Passage Text', validators=[DataRequired()])
    submit = SubmitField('Update Passage')

class GetQuestionForm(FlaskForm):
    question_id = StringField('Question ID', validators=[DataRequired()])


class GetPassageForm(FlaskForm):
    passage_id = StringField('Passage ID', validators=[DataRequired()])

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Check if the username and password match the users table
        cursor = db.cursor()
        query = "SELECT * FROM users WHERE username = %s AND password = %s"
        values = (username, password)
        cursor.execute(query, values)
        user = cursor.fetchone()

        if user:
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html', form=form)

@app.route('/home', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/list_questions', methods=['GET'])
def list_questions():
    questions = admin_interface.get_all_questions()  # Assuming this function fetches all questions
    return render_template('list_questions.html', questions=questions)


@app.route('/add_question', methods=['GET', 'POST'])
def add_question():
    form = QuestionForm()
    subsection_choices = {
        'Mathematics': [
            ('3d_geometry', '3d_geometry'),
            ('permutations_combinations', 'Permutations and Combinations'),
            ('probability', 'Probability'),
            ('sequence_series', 'Sequence and Series'),
            ('trigonometry', 'Trigonometry'),
            ('inverse_trigonometry', 'Inverse Trigonometry'),
            ('geometry_circles_triangles', 'Geometry - Circles and Triangles')
        ],
        'physics': [
            ('laws_of_motion', 'Laws of Motion'),
            ('work_energy_power', 'Work, Energy, Power'),
            ('gravitation', 'Gravitation'),
            ('properties_solids_fluids', 'Properties of Solids and Fluids'),
            ('electrostatics', 'Electrostatics'),
            ('current_electricity', 'Current Electricity'),
            ('magnetism', 'Magnetic Effect of Current and Magnetism')
        ],
        'english': [
            ('antonyms', 'Antonyms'),
            ('synonyms', 'Synonyms'),
            ('passage', 'Passage'),
            ('grammar', 'Grammar'),
            ('idioms', 'Idioms')
        ],
        'reasoning': [
            ('numerical_reasoning', 'Numerical Reasoning'),
            ('verbal_reasoning', 'Verbal Reasoning')
        ]
    }

    if request.method == 'POST':
        selected_section = request.form.get('section')
        if selected_section and selected_section in subsection_choices:
            form.subsection.choices = subsection_choices[selected_section]
            
        print("Form data:", request.form)
        if form.validate_on_submit():
            question_text = form.question_text.data
            section = form.section.data
            subsection = form.subsection.data
            passage_id = form.passage_id.data if form.passage_id.data else None

            # Add the question to the database
            question_id = admin_interface.add_question(question_text, section, subsection, passage_id)

            # Add options to the database
            for option_form in form.options.entries:
                option_text = option_form.option_text.data
                is_correct = option_form.is_correct.data
                admin_interface.add_option(question_id, option_text, is_correct)

            flash('Question and options added successfully.', 'success')
            return redirect(url_for('index'))
        else:
            # Form validation failed, re-render the template with errors
            print("Validation errors:", form.errors)
            return render_template('question_form.html', form=form)

    # If it's a GET request, render the form with initial values
    # form.options.entries = [FormField(OptionForm()) for _ in range(4)]  # Initialize with 4 option fields
    return render_template('question_form.html', form=form)

# Define a route for the success page
@app.route('/success')
def success():
    return "Question added successfully!"


@app.route('/add_passage', methods=['GET', 'POST'])
def add_passage():
    form = PassageForm()
    print("Form data:", request.form)
    if form.validate_on_submit():
        passage_text = form.passage_text.data
        passage_id = admin_interface.add_passage(passage_text)
        flash(f'Passage added with ID: {passage_id}', 'success')
        return redirect(url_for('index'))
    else: 
        print("Validation errors:", form.errors)
    return render_template('add_passage.html', form=form)



@app.route('/update_passage', methods=['GET', 'POST'])
def update_passage():
    form = UpdatePassageForm()
    if form.validate_on_submit():
        passage_id = form.passage_id.data
        new_passage_text = form.passage_text.data
        admin_interface.update_passage(int(passage_id), new_passage_text)
        flash('Passage updated successfully.', 'success')
        return redirect(url_for('index'))
    return render_template('update_passage.html', form=form)


@app.route('/delete_passage', methods=['GET', 'POST'])
def delete_passage():
    form = DeletePassageForm()
    if form.validate_on_submit():
        passage_id = form.passage_id.data
        admin_interface.delete_passage(int(passage_id))
        flash('Passage deleted successfully.', 'success')
        return redirect(url_for('index'))
    return render_template('delete_passage.html', form=form)

@app.route('/list_passages', methods=['GET'])
def list_passages():
    # cursor = db.cursor()
    # cursor.execute("SELECT passage_id, passage_text FROM passages")
    # passages = cursor.fetchall()
    passages = admin_interface.get_all_passages()
    return render_template('list_passages.html', passages=passages)


@app.route('/update_question', methods=['GET', 'POST'])
def update_question():
    form = UpdateQuestionForm()
    if form.validate_on_submit():
        question_id = form.question_id.data
        question_text = form.question_text.data
        section = form.section.data
        subsection = form.subsection.data

        admin_interface.update_question(int(question_id), question_text, section, subsection)
        flash('Question updated successfully.', 'success')
        return redirect(url_for('index'))

    # If it's a GET request, populate the form with the existing question data
    if request.method == 'GET':
        question_id = request.args.get('question_id')
        if question_id:
            question = admin_interface.get_question(int(question_id))
            if question:
                form.question_id.data = question_id
                form.question_text.data = question['question_text']
                form.section.data = question['section']
                form.subsection.data = question['subsection']

    return render_template('update_question.html', form=form)


@app.route('/delete_question', methods=['GET', 'POST'])
def delete_question():
    form = DeleteQuestionForm()
    if form.validate_on_submit():
        question_id = form.question_id.data
        admin_interface.delete_question(int(question_id))
        flash('Question deleted successfully.', 'success')
        return redirect(url_for('index'))
    return render_template('delete_question.html', form=form)

@app.route('/get_question', methods=['GET', 'POST'])
def get_question():
    form = GetQuestionForm()
    if form.validate_on_submit():
        question_id = form.question_id.data
        if question_id:
            question = admin_interface.get_question(int(question_id))
            if question:
                print("Question data:", question)  # Add this line
                return render_template('question_detail.html', question=question)
            else:
                flash('Question not found.', 'error')
        else:
            flash('Question ID is required.', 'error')

    return render_template('get_question.html', form=form)


@app.route('/get_passage', methods=['GET', 'POST'])
def get_passage():
    form = GetPassageForm()
    if form.validate_on_submit():
        passage_id = form.passage_id.data
        if passage_id:
            passage_text = get_passage_text(int(passage_id))
            if passage_text:
                return render_template('passage_detail.html', passage_text=passage_text)
            else:
                flash('Passage not found.', 'error')
        else:
            flash('Passage ID is required.', 'error')

    return render_template('get_passage.html', form=form)

@app.route('/add_option', methods=['GET', 'POST'])
def add_option():
    form = AddOptionForm()
    if form.validate_on_submit():
        question_id = form.question_id.data
        option_text = form.option_text.data
        is_correct = form.is_correct.data
        admin_interface.add_option(int(question_id), option_text, is_correct)
        flash('Option added successfully.', 'success')
        return redirect(url_for('index'))
    return render_template('add_option.html', form=form)


@app.route('/update_option', methods=['GET', 'POST'])
def update_option():
    form = UpdateOptionForm()
    if form.validate_on_submit():
        option_id = form.option_id.data
        option_text = form.option_text.data
        is_correct = form.is_correct.data
        admin_interface.update_option(int(option_id), option_text, is_correct)
        flash('Option updated successfully.', 'success')
        return redirect(url_for('index'))
    return render_template('update_option.html', form=form)


@app.route('/delete_option', methods=['GET', 'POST'])
def delete_option():
    form = DeleteOptionForm()
    if form.validate_on_submit():
        option_id = form.option_id.data
        admin_interface.delete_option(int(option_id))
        flash('Option deleted successfully.', 'success')
        return redirect(url_for('index'))
    return render_template('delete_option.html', form=form)

@app.route('/upload_image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return 'No image uploaded', 400

    image_file = request.files['image']
    if image_file.filename == '':
        return 'No image selected', 400

    if request.form.get('upload_type') == 'question_image':
        question_id = request.form.get('question_id')
        if question_id:
            image_data = image_file.read()
            admin_interface.add_or_update_question_image(int(question_id), image_data)
            flash('Question image uploaded successfully.', 'success')
        else:
            return 'Question ID is required.', 400

    elif request.form.get('upload_type') == 'option_image':
        option_id = request.form.get('option_id')
        if option_id:
            image_data = image_file.read()
            admin_interface.add_or_update_option_image(int(option_id), image_data)
            flash('Option image uploaded successfully.', 'success')
        else:
            return 'Option ID is required.', 400

    else:
        return 'Invalid upload type.', 400

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run()
