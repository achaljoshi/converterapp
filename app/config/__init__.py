from flask import Blueprint

config = Blueprint('config', __name__)

from . import routes 

import os

class DefaultConfig:
    SECRET_KEY = 'dev-secret-key'
    # Use relative path for cross-platform compatibility
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'instance', 'app.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FLASK_ENV = 'development'
    # Add other default config values as needed 