from flask import Blueprint

config = Blueprint('config', __name__)

from . import routes 

class DefaultConfig:
    SECRET_KEY = 'dev-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///../instance/app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FLASK_ENV = 'development'
    # Add other default config values as needed 