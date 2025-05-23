# ConverterApp

A comprehensive test case, workflow, and configuration management platform with analytics, scheduling, and universal permissions.

## Features
- Test case, workflow, converter config, file type, and configuration management
- **Test Cases can have multiple workflows, each with its own sample file upload**
- Dynamic UI: Add Workflow button, workflow dropdown, file upload per workflow, remove row
- Bulk execution, scheduling, and analytics dashboards
- Universal, fine-grained permission and role system
- User management (create, edit, deactivate, assign roles)
- Cloning for all major entities
- Audit logging for all actions
- Extensible, modular architecture

## Quickstart

1. **Clone the repo:**
   ```sh
   git clone <repo-url>
   cd converterapp
   ```
2. **Create and activate a virtual environment:**
   ```sh
   python3 -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
4. **Set up the database:**
   ```sh
   flask db upgrade
   ```
5. **Run the app:**
   ```sh
   flask run
   ```

## Directory Structure

```
converterapp/
  app/           # Main Flask app (blueprints, models, templates)
  instance/      # Instance config
  migrations/    # Alembic migrations
  resources/     # Static resources
  scripts/       # Utility scripts
  venv/          # Virtual environment
  DESIGN.md      # Technical design
  WORKFLOW.md    # Business/technical workflows
  API_REFERENCE.md # API endpoints
  README.md      # This file
  requirements.txt
  run.py
```

## Documentation
- [DESIGN.md](DESIGN.md) — Technical architecture, ERD, DFD
- [WORKFLOW.md](WORKFLOW.md) — Business and technical workflows
- [API_REFERENCE.md](API_REFERENCE.md) — API endpoints

---
For contributing, see [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Requirements
- **Python 3.8+** (recommended: Python 3.10 or newer)
- Git

---

## Setup Instructions

### 1. Clone the Repository
```sh
git clone <your-repo-url>
cd converterapp
```

### 2. Create a Virtual Environment
**On Windows:**
```sh
python -m venv venv
venv\Scripts\activate
```
**On Linux/Mac:**
```sh
python3 -m venv venv
source venv/bin/activate
```

> **Note:**  
> The `venv/` folder (your virtual environment) is excluded from version control via `.gitignore`.  
> Each developer should create their own virtual environment locally after cloning the repository.

### 3. Install Dependencies
```sh
pip install -r requirements.txt
```

### 4. Configuration
- Default configuration values (such as `SECRET_KEY`, `SQLALCHEMY_DATABASE_URI`, etc.) are set in `app/config/__init__.py` in the `DefaultConfig` class.
- You **do not need a `.env` file** for local development unless you want to override these defaults.
- To override any config (for production or secrets), set environment variables or create a `.env` file as needed:
  ```
  FLASK_APP=run.py
  FLASK_ENV=production
  SECRET_KEY=your-production-secret
  SQLALCHEMY_DATABASE_URI=sqlite:///instance/app.db
  ```
- **Important:**
  - On **Linux/Mac**, the default `sqlite:///instance/app.db` usually works if you run the app from the project root.
  - On **Windows**, you may need to use an absolute path, e.g.:
    ```
    SQLALCHEMY_DATABASE_URI=sqlite:///C:/Users/youruser/Projects/converterapp/instance/app.db
    ```
  - Make sure the `instance` directory exists in your project root and is writable.

### 5. Initialize the Database
```sh
flask db upgrade
```

### 6. Run the Application
**On Windows:**
```sh
set FLASK_APP=run.py
flask run
```
**On Linux/Mac:**
```sh
export FLASK_APP=run.py
flask run
```
Or, to run with the provided script (all OS):
```sh
python run.py
```

The app will be available at [http://127.0.0.1:5000](http://127.0.0.1:5000) or the port specified in `run.py`.

---

## Notes
- The SQLite database file is created in the `instance/` directory by default.
- To create an admin user, register via the UI and manually update the user role in the database if needed.
- For production, set `FLASK_ENV=production` and use a production-ready WSGI server (e.g., Gunicorn or uWSGI).
- All configuration and extension initialization is handled in `app/__init__.py`.
- **Workflow Audit Log:** All workflow changes are tracked in the database and viewable from the UI.
- **Template Viewing:** TXT and XML templates are viewable as plain text from the File Types page.
- Uploaded files are saved in the `uploads/` directory (auto-created if missing)

---

## Troubleshooting
- If you get migration errors, try deleting the `instance/app.db` file and re-running `flask db upgrade` (this will delete all data).
- Ensure you have Python 3.8+ installed.
- If you see issues with dropdowns or UI, ensure you have an internet connection for Bootstrap CDN.
- If you get `ModuleNotFoundError` for any dependency, ensure you are in the virtual environment and have run `pip install -r requirements.txt`.
- If you change requirements, re-run `pip install -r requirements.txt`.

---

## License
MIT License 