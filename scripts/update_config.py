import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app, db
from app.models import Configuration, AuditLog
import json

app = create_app()

# --- USER: Edit these values for your update ---
CONFIG_NAME = "PACS008"  # or set to None to use FILE_TYPE
FILE_TYPE = None          # or set to e.g. "PACS008"

# New rules and schema (replace with your update)
new_rules = {
    "example_field": {"path": "/def:Document/def:Example"}
    # ... add your updated rules here ...
}
new_schema = {
    "type": "object",
    "properties": {
        "example_field": {"type": "string"}
        # ... add your updated schema here ...
    },
    "required": ["example_field"]
}

with app.app_context():
    # Find the config by name or file_type
    config = None
    if CONFIG_NAME:
        config = Configuration.query.filter_by(name=CONFIG_NAME).first()
    elif FILE_TYPE:
        config = Configuration.query.filter_by(file_type=FILE_TYPE).first()
    if not config:
        print("Configuration not found.")
        sys.exit(1)
    old_rules = config.rules
    old_schema = config.schema
    config.rules = json.dumps(new_rules)
    config.schema = json.dumps(new_schema)
    db.session.commit()
    # Log the update in the audit log
    db.session.add(AuditLog(
        user="script",
        action="update",
        filetype=config.file_type,
        details=f"Automated update for {config.name}\nrules:{json.dumps(new_rules, indent=2, sort_keys=True)}\nschema:{json.dumps(new_schema, indent=2, sort_keys=True)}"
    ))
    db.session.commit()
    print(f"Configuration '{config.name}' updated and audit log entry created.") 