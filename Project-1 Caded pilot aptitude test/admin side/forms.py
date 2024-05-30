from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired


class PassageForm(FlaskForm):
    passage_text = TextAreaField('Passage Text', validators=[DataRequired()])
    submit = SubmitField('Submit')

class QuestionForm(FlaskForm):
    question_text = TextAreaField('Question Text', validators=[DataRequired()])
    section = StringField('Section', validators=[DataRequired()])
    subsection = StringField('Subsection', validators=[DataRequired()])
    passage_id = StringField('Passage ID (leave blank if not related to a passage)')
    submit = SubmitField('Submit')

class OptionForm(FlaskForm):
    option_text = TextAreaField('Option Text', validators=[DataRequired()])
    is_correct = BooleanField('Is Correct?')
    submit = SubmitField('Submit')