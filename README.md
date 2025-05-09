# ConverterApp

A web application for managing file type configurations and converter rules, supporting advanced mapping and schema validation.

---

## Features
- Manage General Configurations (e.g., MT103, Pacs008, pain001)
- Manage Converter Configurations with advanced rules and schema
- User authentication and role-based access
- UI built with Flask, Bootstrap, and JSONEditor

---

## Setup Instructions

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd converterapp
```

### 2. Create a Virtual Environment
#### On **Windows**:
```bash
python -m venv venv
venv\Scripts\activate
```
#### On **Linux/Mac**:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configuration
- Default configuration values (such as `SECRET_KEY`, `SQLALCHEMY_DATABASE_URI`, etc.) are set in `app/config/__init__.py` in the `DefaultConfig` class.
- You **do not need a `.env** file for local development unless you want to override these defaults.
- To override any config (for production or secrets), set environment variables or create a `.env` file as needed:
  ```
  FLASK_APP=run.py
  FLASK_ENV=production
  SECRET_KEY=your-production-secret
  ```

### 5. Initialize the Database
```bash
flask db upgrade
```

### 6. Run the Application
```bash
flask run
```
Or, to run with the provided script:
```bash
python run.py
```

The app will be available at [http://127.0.0.1:5000](http://127.0.0.1:5000) or the port specified in `run.py`.

---

## Notes
- For SQLite, the database file is created in the `instance/` directory.
- To create an admin user, register via the UI and manually update the user role in the database if needed.
- For production, set `FLASK_ENV=production` and use a production-ready WSGI server (e.g., Gunicorn or uWSGI).
- **Circular Import Best Practice:** All configuration and extension initialization is handled in `app/__init__.py`. Imports of config classes (like `DefaultConfig`) are done inside the `create_app` function to avoid circular import errors.

---

## Troubleshooting
- If you get migration errors, try deleting the `instance/app.db` file and re-running `flask db upgrade` (this will delete all data).
- Ensure you have Python 3.8+ installed.
- If you see issues with dropdowns or UI, ensure you have an internet connection for Bootstrap CDN.

---

## License
MIT License 