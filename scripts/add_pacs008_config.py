import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app, db
from app.models import Configuration
import json

app = create_app()

rules = {
    "apphdr_bizmsgid": { "path": "/app:AppHdr/app:BizMsgIdr" },
    "apphdr_msgdefid": { "path": "/app:AppHdr/app:MsgDefIdr" },
    "apphdr_bizsvc":   { "path": "/app:AppHdr/app:BizSvc" },
    "apphdr_created":  { "path": "/app:AppHdr/app:CreDt" },
    "message_id": { "path": "/def:Document/def:FIToFICstmrCdtTrf/def:GrpHdr/def:MsgId" },
    "creation_datetime": { "path": "/def:Document/def:FIToFICstmrCdtTrf/def:GrpHdr/def:CreDtTm" },
    "debtor_name": { "path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:Dbtr/def:Nm" },
    "debtor_account": { "path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:DbtrAcct/def:Id/def:Othr/def:Id" },
    "creditor_name": { "path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:Cdtr/def:Nm" },
    "creditor_account": { "path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:CdtrAcct/def:Id/def:Othr/def:Id" },
    "amount": { "path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:InstdAmt" },
    "currency": { "path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:InstdAmt/@Ccy" },
    "remittance_lines": {
        "path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:RmtInf/def:Ustrd",
        "multiple": True
    },
    "intermediary_agents": {
        "path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:IntrmyAgt1|/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:IntrmyAgt2|/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:IntrmyAgt3",
        "multiple": True,
        "fields": {
            "bic": { "path": "def:FinInstnId/def:BICFI" },
            "name": { "path": "def:FinInstnId/def:Nm" }
        }
    }
}

schema = {
    "type": "object",
    "properties": {
        "apphdr_bizmsgid": { "type": ["string", "null"] },
        "apphdr_msgdefid": { "type": ["string", "null"] },
        "apphdr_bizsvc":   { "type": ["string", "null"] },
        "apphdr_created":  { "type": ["string", "null"] },
        "message_id": { "type": "string" },
        "creation_datetime": { "type": "string" },
        "debtor_name": { "type": "string" },
        "debtor_account": { "type": "string" },
        "creditor_name": { "type": "string" },
        "creditor_account": { "type": "string" },
        "amount": { "type": "string" },
        "currency": { "type": "string" },
        "remittance_lines": {
            "type": "array",
            "items": { "type": "string" }
        },
        "intermediary_agents": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "bic": { "type": "string" },
                    "name": { "type": ["string", "null"] }
                },
                "required": ["bic"]
            }
        }
    },
    "required": [
        "message_id", "creation_datetime", "debtor_name", "debtor_account",
        "creditor_name", "creditor_account", "amount", "currency"
    ]
}

with app.app_context():
    existing = Configuration.query.filter_by(file_type="PACS008").first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
    config = Configuration(
        name="PACS008",
        description="Sample configuration for PACS008 SWIFT/ISO 20022 message.",
        file_type="PACS008",
        rules=json.dumps(rules),
        schema=json.dumps(schema)
    )
    db.session.add(config)
    db.session.commit()
    print("Sample PACS008 configuration added to the database.") 