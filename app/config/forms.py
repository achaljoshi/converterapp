from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired

class ConfigurationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = StringField('Description')
    file_type = SelectField('File Type', coerce=int)
    rules = TextAreaField('Rules (JSON or text)')
    schema = TextAreaField('Rules JSON Schema (optional)')
    submit = SubmitField('Save')

class ConverterConfigForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = StringField('Description')
    source_type = SelectField('Source Type', choices=[], validators=[DataRequired()])
    target_type = SelectField('Target Type', choices=[], validators=[DataRequired()])
    rules = TextAreaField('Rules (JSON)')
    schema = TextAreaField('Schema (JSON)')
    submit = SubmitField('Save') 