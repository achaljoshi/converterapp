import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app, db
from app.models import FileType

app = create_app()

default_filetypes = [
    {"name": "MT103", "description": "SWIFT MT103 message"},
    {"name": "pacs.008", "description": "ISO 20022 pacs.008 message"},
    {"name": "pain.001", "description": "ISO 20022 pain.001 message"}
]

with app.app_context():
    for ft in default_filetypes:
        if not FileType.query.filter_by(name=ft["name"]).first():
            db.session.add(FileType(name=ft["name"], description=ft["description"]))
    db.session.commit()
    print("Default file types seeded.") 