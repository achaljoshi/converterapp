from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Optional, Email

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    role = SelectField('Role', choices=[('admin', 'Admin'), ('analyst', 'Business Analyst'), ('tester', 'Tester'), ('developer', 'Developer')], validators=[DataRequired()])
    submit = SubmitField('Register')

class RoleForm(FlaskForm):
    name = StringField('Role Name', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    submit = SubmitField('Save')

class PermissionForm(FlaskForm):
    name = StringField('Permission Name', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    submit = SubmitField('Save')

class RolePermissionForm(FlaskForm):
    permissions = SelectField('Permissions', coerce=int, choices=[], validators=[DataRequired()])
    submit = SubmitField('Assign')

class UserRoleForm(FlaskForm):
    user = SelectField('User', coerce=int, choices=[], validators=[DataRequired()])
    role = SelectField('Role', coerce=int, choices=[], validators=[DataRequired()])
    submit = SubmitField('Assign')

class UserCreateForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[Optional(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    role = SelectField('Role', coerce=int, choices=[], validators=[DataRequired()])
    submit = SubmitField('Create User')

class UserEditForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[Optional(), Email()])
    password = PasswordField('Password', validators=[Optional()])
    role = SelectField('Role', coerce=int, choices=[], validators=[DataRequired()])
    submit = SubmitField('Update User') 