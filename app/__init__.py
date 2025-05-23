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
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/storezadeveloper/Projects/converterapp/instance/app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_ENABLED'] = False

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    from app.testcases import permission_required

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

    # Simple dashboard route for now
    from flask import render_template
    from flask_login import login_required, current_user
    @app.route('/dashboard')
    @login_required
    @permission_required('dashboard_view')
    def dashboard():
        from app.models import TestCase, TestRun, Workflow
        from sqlalchemy import func
        # KPIs
        total_cases = TestCase.query.count()
        total_runs = TestRun.query.count()
        passed_runs = TestRun.query.filter_by(status='passed').count()
        failed_runs = TestRun.query.filter_by(status='failed').count()
        error_runs = TestRun.query.filter(TestRun.status.notin_(['passed', 'failed'])).count()
        last_run = TestRun.query.order_by(TestRun.executed_at.desc()).first()
        # Recent runs
        recent_runs = (
            TestRun.query.order_by(TestRun.executed_at.desc())
            .limit(10).all()
        )
        # Bar chart: runs by day and status
        runs_by_day = (
            db.session.query(
                func.date(TestRun.executed_at), TestRun.status, func.count()
            ).group_by(func.date(TestRun.executed_at), TestRun.status)
            .order_by(func.date(TestRun.executed_at)).all()
        )
        # Pie chart: pass/fail distribution
        status_counts = (
            db.session.query(TestRun.status, func.count())
            .group_by(TestRun.status).all()
        )
        # Prepare chart data
        bar_labels = sorted(list(set([str(r[0]) for r in runs_by_day])))
        bar_statuses = list(set([r[1] for r in runs_by_day]))
        bar_data = {status: [0]*len(bar_labels) for status in bar_statuses}
        for i, label in enumerate(bar_labels):
            for status in bar_statuses:
                for r in runs_by_day:
                    if str(r[0]) == label and r[1] == status:
                        bar_data[status][i] = r[2]
        pie_labels = [s[0].capitalize() for s in status_counts]
        pie_data = [s[1] for s in status_counts]
        return render_template(
            'dashboard.html',
            user=current_user,
            total_cases=total_cases,
            total_runs=total_runs,
            passed_runs=passed_runs,
            failed_runs=failed_runs,
            error_runs=error_runs,
            last_run=last_run,
            recent_runs=recent_runs,
            bar_labels=bar_labels,
            bar_statuses=bar_statuses,
            bar_data=bar_data,
            pie_labels=pie_labels,
            pie_data=pie_data
        )

    @app.route('/')
    def home():
        return 'Hello, world! The server is running.'

    return app 

if __name__ == '__main__':
    app.run(debug=True, port=5050) 