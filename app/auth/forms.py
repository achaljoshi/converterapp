from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    role = SelectField('Role', choices=[('admin', 'Admin'), ('analyst', 'Business Analyst'), ('tester', 'Tester'), ('developer', 'Developer')], validators=[DataRequired()])
    submit = SubmitField('Register') 