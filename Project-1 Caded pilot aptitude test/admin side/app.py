from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask import render_template, request, redirect, url_for, flash
import admin_interface
import os
from forms import PassageForm, QuestionForm,OptionForm
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired

app = Flask(__name__)
app.config['SECRET_KEY'] = "ciycttuvuvuy"
csrf = CSRFProtect(app)



@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/add_passage', methods=['GET', 'POST'])
def add_passage():
    form = PassageForm()
    if form.validate_on_submit():
        passage_text = form.passage_text.data
        passage_id = admin_interface.add_passage(passage_text)
        flash(f'Passage added with ID: {passage_id}', 'success')
        return redirect(url_for('index'))
    return render_template('add_passage.html', form=form)


@app.route('/update_passage', methods=['GET', 'POST'])
def update_passage():
    form = PassageForm()
    if form.validate_on_submit():
        passage_id = request.form.get('passage_id')
        new_passage_text = form.passage_text.data
        admin_interface.update_passage(int(passage_id), new_passage_text)
        flash('Passage updated successfully.', 'success')
        return redirect(url_for('index'))
    return render_template('update_passage.html', form=form)

@app.route('/delete_passage', methods=['GET', 'POST'])
def delete_passage():
    if request.method == 'POST':
        passage_id = request.form.get('passage_id')
        admin_interface.delete_passage(int(passage_id))
        flash('Passage deleted successfully.', 'success')
        return redirect(url_for('index'))
    return render_template('delete_passage.html')

@app.route('/add_question', methods=['GET', 'POST'])
def add_question():
    form = QuestionForm()
    if form.validate_on_submit():
        question_text = form.question_text.data
        section = form.section.data
        subsection = form.subsection.data
        passage_id = form.passage_id.data if form.passage_id.data else None
        if passage_id:
            passage_id = int(passage_id)
        question_id = admin_interface.add_question(question_text, section, subsection, passage_id)
        flash(f'Question added with ID: {question_id}', 'success')
        return redirect(url_for('index'))
    return render_template('add_question.html', form=form)

@app.route('/update_question', methods=['GET', 'POST'])
def update_question():
    form = QuestionForm()
    if form.validate_on_submit():
        question_id = request.form.get('question_id')
        question_text = form.question_text.data
        section = form.section.data
        subsection = form.subsection.data
        admin_interface.update_question(int(question_id), question_text, section, subsection)
        flash('Question updated successfully.', 'success')
        return redirect(url_for('index'))
    return render_template('update_question.html', form=form)

@app.route('/delete_question', methods=['GET', 'POST'])
def delete_question():
    if request.method == 'POST':
        question_id = request.form.get('question_id')
        admin_interface.delete_question(int(question_id))
        flash('Question deleted successfully.', 'success')
        return redirect(url_for('index'))
    return render_template('delete_question.html')

@app.route('/add_option', methods=['GET', 'POST'])
def add_option():
    form = OptionForm()
    if form.validate_on_submit():
        question_id = request.form.get('question_id')
        option_text = form.option_text.data
        is_correct = form.is_correct.data
        admin_interface.add_option(int(question_id), option_text, is_correct)
        flash('Option added successfully.', 'success')
        return redirect(url_for('index'))
    return render_template('add_option.html', form=form)

@app.route('/update_option', methods=['GET', 'POST'])
def update_option():
    form = OptionForm()
    if form.validate_on_submit():
        option_id = request.form.get('option_id')
        option_text = form.option_text.data
        is_correct = form.is_correct.data
        admin_interface.update_option(int(option_id), option_text, is_correct)
        flash('Option updated successfully.', 'success')
        return redirect(url_for('index'))
    return render_template('update_option.html', form=form)

@app.route('/delete_option', methods=['GET', 'POST'])
def delete_option():
    if request.method == 'POST':
        option_id = request.form.get('option_id')
        admin_interface.delete_option(int(option_id))
        flash('Option deleted successfully.', 'success')
        return redirect(url_for('index'))
    return render_template('delete_option.html')

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