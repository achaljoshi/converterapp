from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import json

# Initialize extensions
login_manager = LoginManager()
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    from app.config import DefaultConfig  # moved here to avoid circular import
    app = Flask(__name__)
    app.config.from_object(DefaultConfig)
    app.config['SECRET_KEY'] = 'your-secret-key'  # Change this in production
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/storezadeveloper/Projects/converterapp/instance/app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_ENABLED'] = False

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'

    # Add custom Jinja2 filter for JSON parsing
    @app.template_filter('from_json')
    def from_json_filter(value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return []
        return value

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .testcases import permission_required

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

    from .testcases import testcases as testcases_blueprint
    app.register_blueprint(testcases_blueprint)

    from .git_repos import git_repos as git_repos_blueprint
    app.register_blueprint(git_repos_blueprint)

    from .labels import labels as labels_blueprint
    app.register_blueprint(labels_blueprint)

    from .frameworks import frameworks as frameworks_blueprint
    app.register_blueprint(frameworks_blueprint)

    # Simple dashboard route for now
    from flask import render_template
    from flask_login import login_required, current_user
    from .models import TestCase, TestRun, GitRepository, TestFramework, Label
    from .auth.routes import admin_or_permission_required

    @app.route('/dashboard')
    @login_required
    @admin_or_permission_required('dashboard_view')
    def dashboard():
        total_cases = TestCase.query.count()
        total_runs = TestRun.query.count()
        total_repos = GitRepository.query.count()
        total_frameworks = TestFramework.query.count()
        total_labels = Label.query.count()
        
        # Get recent test runs
        recent_runs = TestRun.query.order_by(TestRun.executed_at.desc()).limit(5).all()
        
        # Get last run
        last_run = TestRun.query.order_by(TestRun.executed_at.desc()).first()
        
        # Calculate run statistics
        passed_runs = TestRun.query.filter_by(status='passed').count()
        failed_runs = TestRun.query.filter_by(status='failed').count()
        error_runs = TestRun.query.filter(TestRun.status.notin_(['passed', 'failed'])).count()
        
        # Prepare chart data (simplified for now)
        bar_labels = ['Today', 'Yesterday', '2 days ago', '3 days ago', '4 days ago']
        bar_datasets = [{
            'label': 'Passed',
            'data': [passed_runs, 0, 0, 0, 0],
            'backgroundColor': '#198754'
        }, {
            'label': 'Failed', 
            'data': [failed_runs, 0, 0, 0, 0],
            'backgroundColor': '#dc3545'
        }, {
            'label': 'Error',
            'data': [error_runs, 0, 0, 0, 0], 
            'backgroundColor': '#ffc107'
        }]
        
        pie_labels = ['Passed', 'Failed', 'Error']
        pie_data = [passed_runs, failed_runs, error_runs]
        
        return render_template('dashboard.html', 
                             total_cases=total_cases,
                             total_runs=total_runs,
                             total_repos=total_repos,
                             total_frameworks=total_frameworks,
                             total_labels=total_labels,
                             recent_runs=recent_runs,
                             last_run=last_run,
                             passed_runs=passed_runs,
                             failed_runs=failed_runs,
                             error_runs=error_runs,
                             bar_labels=bar_labels,
                             bar_datasets=bar_datasets,
                             pie_labels=pie_labels,
                             pie_data=pie_data)

    @app.route('/')
    def home():
        return 'Hello, world! The server is running.'

    return app 

if __name__ == '__main__':
    app.run(debug=True, port=5050) 