import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app, db
from app.models import Configuration
import json

app = create_app()

rules = {
    # AppHdr fields
    "apphdr_fr_bic": {"path": "/app:AppHdr/app:Fr/app:FIId/app:FinInstnId/app:BICFI"},
    "apphdr_to_bic": {"path": "/app:AppHdr/app:To/app:FIId/app:FinInstnId/app:BICFI"},
    "apphdr_bizmsgid": {"path": "/app:AppHdr/app:BizMsgIdr"},
    "apphdr_msgdefid": {"path": "/app:AppHdr/app:MsgDefIdr"},
    "apphdr_bizsvc":   {"path": "/app:AppHdr/app:BizSvc"},
    "apphdr_created":  {"path": "/app:AppHdr/app:CreDt"},
    # Document/GrpHdr fields
    "message_id": {"path": "/def:Document/def:FIToFICstmrCdtTrf/def:GrpHdr/def:MsgId"},
    "creation_datetime": {"path": "/def:Document/def:FIToFICstmrCdtTrf/def:GrpHdr/def:CreDtTm"},
    "number_of_txs": {"path": "/def:Document/def:FIToFICstmrCdtTrf/def:GrpHdr/def:NbOfTxs"},
    "settlement_method": {"path": "/def:Document/def:FIToFICstmrCdtTrf/def:GrpHdr/def:SttlmInf/def:SttlmMtd"},
    # CdtTrfTxInf fields
    "amount": { "path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:InstdAmt" },
    "currency": { "path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:InstdAmt/@Ccy" },
    "instr_id": {"path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:PmtId/def:InstrId"},
    "end_to_end_id": {"path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:PmtId/def:EndToEndId"},
    "uetr": {"path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:PmtId/def:UETR"},
    "service_level": {"path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:PmtTpInf/def:SvcLvl/def:Cd"},
    "intrbk_sttlm_amt": {"path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:IntrBkSttlmAmt"},
    "intrbk_sttlm_ccy": {"path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:IntrBkSttlmAmt/@Ccy"},
    "intrbk_sttlm_dt": {"path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:IntrBkSttlmDt"},
    "instd_amt": {"path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:InstdAmt"},
    "instd_ccy": {"path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:InstdAmt/@Ccy"},
    "charge_bearer": {"path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:ChrgBr"},
    # Agents
    "prvs_instg_agt1_bic": {"path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:PrvsInstgAgt1/def:FinInstnId/def:BICFI"},
    "instg_agt_bic": {"path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:InstgAgt/def:FinInstnId/def:BICFI"},
    "instd_agt_bic": {"path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:InstdAgt/def:FinInstnId/def:BICFI"},
    "intrmy_agt1_bic": {"path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:IntrmyAgt1/def:FinInstnId/def:BICFI"},
    # Debtor/Creditor
    "debtor_name": {"path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:Dbtr/def:Nm"},
    "debtor_address": {"path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:Dbtr/def:PstlAdr/def:AdrLine", "multiple": True},
    "debtor_account": {"path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:DbtrAcct/def:Id/def:Othr/def:Id"},
    "debtor_agent_bic": {"path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:DbtrAgt/def:FinInstnId/def:BICFI"},
    "creditor_agent_bic": {"path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:CdtrAgt/def:FinInstnId/def:BICFI"},
    "creditor_name": {"path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:Cdtr/def:Nm"},
    "creditor_address": {"path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:Cdtr/def:PstlAdr/def:AdrLine", "multiple": True},
    "creditor_account": {"path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:CdtrAcct/def:Id/def:Othr/def:Id"},
    # Instructions and remittance
    "instr_for_nxt_agt": {"path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:InstrForNxtAgt/def:InstrInf"},
    "remittance_lines": {"path": "/def:Document/def:FIToFICstmrCdtTrf/def:CdtTrfTxInf/def:RmtInf/def:Ustrd", "multiple": True}
}

schema = {
    "type": "object",
    "properties": {
        "apphdr_fr_bic": {"type": ["string", "null"]},
        "apphdr_to_bic": {"type": ["string", "null"]},
        "apphdr_bizmsgid": {"type": ["string", "null"]},
        "apphdr_msgdefid": {"type": ["string", "null"]},
        "apphdr_bizsvc":   {"type": ["string", "null"]},
        "apphdr_created":  {"type": ["string", "null"]},
        "message_id": {"type": ["string", "null"]},
        "creation_datetime": {"type": ["string", "null"]},
        "number_of_txs": {"type": ["string", "null"]},
        "settlement_method": {"type": ["string", "null"]},
        "amount": { "type": "string" },
        "currency": { "type": "string" },
        "instr_id": {"type": ["string", "null"]},
        "end_to_end_id": {"type": ["string", "null"]},
        "uetr": {"type": ["string", "null"]},
        "service_level": {"type": ["string", "null"]},
        "intrbk_sttlm_amt": {"type": ["string", "null"]},
        "intrbk_sttlm_ccy": {"type": ["string", "null"]},
        "intrbk_sttlm_dt": {"type": ["string", "null"]},
        "instd_amt": {"type": ["string", "null"]},
        "instd_ccy": {"type": ["string", "null"]},
        "charge_bearer": {"type": ["string", "null"]},
        "prvs_instg_agt1_bic": {"type": ["string", "null"]},
        "instg_agt_bic": {"type": ["string", "null"]},
        "instd_agt_bic": {"type": ["string", "null"]},
        "intrmy_agt1_bic": {"type": ["string", "null"]},
        "debtor_name": {"type": ["string", "null"]},
        "debtor_address": {"type": "array", "items": {"type": "string"}},
        "debtor_account": {"type": ["string", "null"]},
        "debtor_agent_bic": {"type": ["string", "null"]},
        "creditor_agent_bic": {"type": ["string", "null"]},
        "creditor_name": {"type": ["string", "null"]},
        "creditor_address": {"type": "array", "items": {"type": "string"}},
        "creditor_account": {"type": ["string", "null"]},
        "instr_for_nxt_agt": {"type": ["string", "null"]},
        "remittance_lines": {"type": "array", "items": {"type": "string"}}
    },
    "required": [
        "apphdr_bizmsgid", "apphdr_msgdefid", "message_id", "creation_datetime",
        "debtor_name", "debtor_account", "creditor_name", "creditor_account", "amount", "currency"
    ]
}

with app.app_context():
    existing = Configuration.query.filter_by(file_type="PACS008").first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
    config = Configuration(
        name="PACS008_FULL",
        description="Full extraction for PACS008 SWIFT/ISO 20022 message.",
        file_type="PACS008",
        rules=json.dumps(rules),
        schema=json.dumps(schema)
    )
    db.session.add(config)
    db.session.commit()
    print("Full PACS008 configuration added to the database.") 