import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app, db
from app.models import Configuration
import json

app = create_app()

rules = {
    "block1": {"block": 1},
    "block2": {"block": 2},
    "transaction_reference": {
        "path": ":20:"
    },
    "bank_operation_code": {
        "path": ":23B:"
    },
    "value_date_currency_amount": {
        "path": ":32A:"
    },
    "amount": {
        "path": ":33B:"
    },
    "ordering_customer": {
        "path": ":50K:",
        "multiple": True,
        "postprocess": "account_lines"
    },
    "ordering_institution": {
        "path": ":52A:"
    },
    "intermediary_institution": {
        "path": ":56A:"
    },
    "account_with_institution": {
        "path": ":57A:"
    },
    "beneficiary_customer": {
        "path": ":59:",
        "multiple": True,
        "postprocess": "account_lines"
    },
    "remittance_info": {
        "path": ":70:",
        "multiple": True,
        "postprocess": "remittance_lines"
    },
    "details_of_charges": {
        "path": ":71A:"
    },
    "sender_to_receiver_info": {
        "path": ":72:",
        "multiple": True
    }
}

schema = {
    "type": "object",
    "properties": {
        "block1": {"type": ["string", "null"]},
        "block2": {"type": ["string", "null"]},
        "transaction_reference": {"type": "string"},
        "bank_operation_code": {"type": ["string", "null"]},
        "value_date_currency_amount": {"type": ["string", "null"]},
        "amount": {"type": ["string", "null"]},
        "ordering_customer": {
            "oneOf": [
                {
                    "type": "object",
                    "properties": {
                        "account_number": {"type": ["string", "null"]},
                        "lines": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["account_number", "lines"]
                },
                {"type": "array", "items": {"type": "string"}},
                {"type": "string"},
                {"type": "null"}
            ]
        },
        "ordering_institution": {"type": ["string", "null"]},
        "intermediary_institution": {"type": ["string", "null"]},
        "account_with_institution": {"type": ["string", "null"]},
        "beneficiary_customer": {
            "oneOf": [
                {
                    "type": "object",
                    "properties": {
                        "account_number": {"type": ["string", "null"]},
                        "lines": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["account_number", "lines"]
                },
                {"type": "array", "items": {"type": "string"}},
                {"type": "string"},
                {"type": "null"}
            ]
        },
        "remittance_info": {
            "oneOf": [
                {"type": "array", "items": {"type": "string"}},
                {"type": "string"},
                {"type": "null"}
            ]
        },
        "details_of_charges": {"type": ["string", "null"]},
        "sender_to_receiver_info": {
            "oneOf": [
                {"type": "array", "items": {"type": "string"}},
                {"type": "string"},
                {"type": "null"}
            ]
        }
    },
    "required": [
        "block1", "block2", "transaction_reference", "bank_operation_code", "value_date_currency_amount", "amount", "ordering_customer", "beneficiary_customer"
    ]
}

with app.app_context():
    existing = Configuration.query.filter_by(file_type="MT103").first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
    config = Configuration(
        name="MT103",
        description="Sample configuration for MT103 SWIFT message.",
        file_type="MT103",
        rules=json.dumps(rules),
        schema=json.dumps(schema)
    )
    db.session.add(config)
    db.session.commit()
    print("Sample MT103 configuration added to the database.") 