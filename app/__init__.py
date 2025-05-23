from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate

# Initialize extensions
login_manager = LoginManager()
db = SQLAlchemy()
csrf = CSRFProtect()
migrate = Migrate()

def create_app():
    from app.config import DefaultConfig  # moved here to avoid circular import
    app = Flask(__name__)
    app.config.from_object(DefaultConfig)
    app.config['SECRET_KEY'] = 'your-secret-key'  # Change this in production
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:/Projects/converterapp/instance/app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_ENABLED'] = False

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .config import config as config_blueprint
    app.register_blueprint(config_blueprint)
    # Register Jinja filters for config blueprint
    from app.config.routes import init_app as config_init_app
    config_init_app(app)

    from .config.routes import filetypes as filetypes_blueprint
    app.register_blueprint(filetypes_blueprint)

    from .config.routes import converters
    app.register_blueprint(converters)

    # Simple dashboard route for now
    from flask import render_template
    from flask_login import login_required, current_user
    @app.route('/dashboard')
    @login_required
    def dashboard():
        return render_template('dashboard.html', user=current_user)

    @app.route('/')
    def home():
        return 'Hello, world! The server is running.'

    return app 

if __name__ == '__main__':
    app.run(debug=True, port=5050) 