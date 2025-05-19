from flask import render_template, redirect, url_for, flash, request, abort, g, jsonify, send_from_directory, current_app, send_file
from flask_login import login_required, current_user
from . import config
from ..models import Configuration, FileType, AuditLog, Workflow, ConverterConfig
from .. import db
# from .forms import ConverterConfigForm  # forms.py has been deleted
import json
from jsonschema import validate as jsonschema_validate, ValidationError as JsonSchemaValidationError
from werkzeug.utils import secure_filename
import os
import tempfile
import re
import logging
from flask import Blueprint
import difflib
from markupsafe import Markup
import csv
from flask import Response
import io
from lxml import etree

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@config.route('/config')
@login_required
@admin_required
def configuration():
    configs = Configuration.query.all()
    return render_template('config.html', configs=configs)

@config.route('/config/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_configuration():
    form = ConfigurationForm()
    # Populate file_type choices from FileType table
    form.file_type.choices = [(ft.id, ft.name) for ft in FileType.query.order_by(FileType.name).all()]
    if form.validate_on_submit():
        # Validate rules as JSON
        rules_data = form.rules.data
        schema_data = form.schema.data
        if rules_data:
            try:
                json.loads(rules_data)
            except json.JSONDecodeError:
                flash('Rules must be valid JSON.')
                return render_template('config_form.html', form=form, action='Add')
        if schema_data:
            try:
                json.loads(schema_data)
            except json.JSONDecodeError:
                flash('Schema must be valid JSON.')
                return render_template('config_form.html', form=form, action='Add')
        # Get file type name from selected id
        file_type_obj = FileType.query.get(form.file_type.data)
        config_obj = Configuration(
            name=form.name.data,
            description=form.description.data,
            file_type=file_type_obj.name if file_type_obj else '',
            rules=rules_data,
            schema=schema_data
        )
        db.session.add(config_obj)
        db.session.commit()
        # Audit log for add (store pretty-printed rules and schema)
        rules_pretty = json.dumps(json.loads(rules_data), indent=2, sort_keys=True) if rules_data else ''
        schema_pretty = json.dumps(json.loads(schema_data), indent=2, sort_keys=True) if schema_data else ''
        db.session.add(AuditLog(
            user=current_user.username,
            action='add',
            filetype=config_obj.file_type,
            details=f"Added configuration: {config_obj.name}\nrules:{rules_pretty}\nschema:{schema_pretty}"
        ))
        db.session.commit()
        flash('Configuration added successfully!')
        return redirect(url_for('config.configuration'))
    return render_template('config_form.html', form=form, action='Add')

@config.route('/config/edit/<int:config_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_configuration(config_id):
    config_obj = Configuration.query.get_or_404(config_id)
    form = ConfigurationForm(obj=config_obj)
    # Populate file_type choices from FileType table
    form.file_type.choices = [(ft.id, ft.name) for ft in FileType.query.order_by(FileType.name).all()]
    # Set default selected value
    if request.method == 'GET':
        file_type_obj = FileType.query.filter_by(name=config_obj.file_type).first()
        if file_type_obj:
            form.file_type.data = file_type_obj.id
    if form.validate_on_submit():
        # Validate rules as JSON
        rules_data = form.rules.data
        schema_data = form.schema.data
        if rules_data:
            try:
                json.loads(rules_data)
            except json.JSONDecodeError:
                flash('Rules must be valid JSON.')
                return render_template('config_form.html', form=form, action='Edit')
        if schema_data:
            try:
                json.loads(schema_data)
            except json.JSONDecodeError:
                flash('Schema must be valid JSON.')
                return render_template('config_form.html', form=form, action='Edit')
        # Get file type name from selected id
        file_type_obj = FileType.query.get(form.file_type.data)
        old_name = config_obj.name
        old_desc = config_obj.description
        old_file_type = config_obj.file_type
        old_rules = config_obj.rules
        old_schema = config_obj.schema
        config_obj.name = form.name.data
        config_obj.description = form.description.data
        config_obj.file_type = file_type_obj.name if file_type_obj else ''
        config_obj.rules = rules_data
        config_obj.schema = schema_data
        db.session.commit()
        # Audit log for edit (store pretty-printed rules and schema)
        rules_pretty = json.dumps(json.loads(rules_data), indent=2, sort_keys=True) if rules_data else ''
        schema_pretty = json.dumps(json.loads(schema_data), indent=2, sort_keys=True) if schema_data else ''
        db.session.add(AuditLog(
            user=current_user.username,
            action='edit',
            filetype=config_obj.file_type,
            details=f"Edited configuration: {old_name} -> {config_obj.name}, {old_desc} -> {config_obj.description}, filetype: {old_file_type} -> {config_obj.file_type}, rules/schema changed: {old_rules != rules_data or old_schema != schema_data}\nrules:{rules_pretty}\nschema:{schema_pretty}"
        ))
        db.session.commit()
        flash('Configuration updated successfully!')
        return redirect(url_for('config.configuration'))
    return render_template('config_form.html', form=form, action='Edit')

@config.route('/config/delete/<int:config_id>', methods=['POST'])
@login_required
@admin_required
def delete_configuration(config_id):
    config_obj = Configuration.query.get_or_404(config_id)
    db.session.delete(config_obj)
    db.session.commit()
    # Audit log for delete
    db.session.add(AuditLog(
        user=current_user.username,
        action='delete',
        filetype=config_obj.file_type,
        details=f"Deleted configuration: {config_obj.name}"
    ))
    db.session.commit()
    flash('Configuration deleted successfully!')
    return redirect(url_for('config.configuration'))

@config.route('/config/test/<int:config_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def test_extraction(config_id):
    config_obj = Configuration.query.get_or_404(config_id)
    extracted = None
    validation_result = None
    error = None
    if request.method == 'POST':
        file = request.files.get('sample_file')
        if not file:
            flash('Please upload a file to test.')
            return redirect(request.url)
        filename = secure_filename(file.filename)
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, filename)
        file.save(file_path)
        try:
            schema_type = request.form.get('schema_type', 'json').lower()
            # Determine file type and extraction logic
            if schema_type == 'text' or config_obj.file_type.lower().startswith('mt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                extracted = extract_mt_fields(content, config_obj.rules)
            elif schema_type == 'xml' or config_obj.file_type.lower().endswith('.xml') or config_obj.file_type.lower().startswith('pacs') or config_obj.file_type.lower().startswith('pain') or filename.lower().endswith('.xml'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                extracted = extract_xml_fields(content, config_obj.rules)
            else:
                error = 'Unsupported file type for extraction.'
            # Debug log for extracted output
            print('Extracted:', extracted)
            # Custom check for required fields (must not be None, empty string, empty list, or empty dict)
            if extracted and config_obj.schema:
                try:
                    schema_json = json.loads(config_obj.schema)
                    required_fields = schema_json.get('required', [])
                    missing = [f for f in required_fields if extracted.get(f) in (None, '', [], {})]
                    if missing:
                        validation_result = f"Invalid: Required field(s) missing or empty: {', '.join(missing)}"
                        extracted = None  # Do not show extracted output
                    else:
                        jsonschema_validate(instance=extracted, schema=schema_json)
                        validation_result = 'Valid! Extracted data matches the schema.'
                except JsonSchemaValidationError as ve:
                    validation_result = f'Invalid: {ve.message}'
                except Exception as e:
                    validation_result = f'Error in validation: {e}'
        except Exception as e:
            error = str(e)
        finally:
            os.remove(file_path)
            os.rmdir(temp_dir)
    return render_template('test_extraction.html', config=config_obj, extracted=extracted, validation_result=validation_result, error=error)

def apply_condition(extracted_value, condition, cond_value):
    if extracted_value is None:
        return None
    if condition == 'contains':
        return extracted_value if cond_value in extracted_value else None
    elif condition == 'equals':
        return extracted_value if extracted_value == cond_value else None
    elif condition == 'not_equals':
        return extracted_value if extracted_value != cond_value else None
    elif condition == 'starts_with':
        return extracted_value if extracted_value.startswith(cond_value) else None
    elif condition == 'ends_with':
        return extracted_value if extracted_value.endswith(cond_value) else None
    elif condition == 'regex':
        import re
        return extracted_value if re.search(cond_value, extracted_value) else None
    return extracted_value

def parse_swift_tags(content):
    """
    Returns a dict: {tag: [list of values for that tag]}
    Handles edge cases per SWIFT rules.
    """
    import re
    tag_dict = {}
    current_tag = None
    current_value_lines = []
    # Normalize line endings and handle end-of-block
    lines = content.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    for line in lines:
        # End of block marker
        if line.strip() == '-}':
            break
        # Tag detection (allow for leading whitespace, case-insensitive)
        tag_match = re.match(r'^\s*(:[0-9A-Za-z]{2,3}:)', line)
        if tag_match:
            # Save previous tag's value
            if current_tag is not None:
                if current_tag not in tag_dict:
                    tag_dict[current_tag] = []
                tag_dict[current_tag].append('\n'.join(current_value_lines).rstrip('\n'))
            # Start new tag
            current_tag = tag_match.group(1)
            value = line[line.find(current_tag) + len(current_tag):]
            current_value_lines = [value] if value.strip() or value == '' else []
        elif current_tag is not None:
            # Continuation line: preserve leading spaces
            if line.strip() != '' or (line == '' and current_value_lines):
                current_value_lines.append(line)
    # Save last tag
    if current_tag is not None:
        if current_tag not in tag_dict:
            tag_dict[current_tag] = []
        tag_dict[current_tag].append('\n'.join(current_value_lines).rstrip('\n'))
    return tag_dict

def parse_remittance_lines(lines):
    """
    Given a list of remittance lines, returns a list of dicts with key-value pairs.
    Handles /KEY/VALUE, /KEY, and value-only segments (assigns to previous key).
    """
    parsed = []
    for line in lines:
        d = {}
        last_key = None
        # Split by '///' or '//' (SWIFT can use both)
        segments = re.split(r'/+', line)
        segments = [seg for seg in segments if seg]  # Remove empty
        i = 0
        while i < len(segments):
            key = segments[i]
            if i + 1 < len(segments):
                value = segments[i + 1]
                d[key] = value
                last_key = key
                i += 2
            else:
                # If only a key left, treat as key with None value
                d[key] = None
                i += 1
        if d:
            parsed.append(d)
    return parsed

def process_account_lines(lines):
    """
    For :50K: and :59: fields, extract the account number from the first line if it starts with a slash.
    Return a dict: {'account_number': ..., 'lines': [...]}.
    """
    if not lines or not isinstance(lines, list):
        return None
    account_number = None
    rest_lines = lines[:]
    if lines and lines[0].startswith('/'):
        account_number = lines[0][1:]
        rest_lines = lines[1:]
    return {'account_number': account_number, 'lines': rest_lines}

def extract_mt_fields(content, rules_json):
    print('DEBUG: rules_json =', rules_json)
    import json
    import re
    try:
        rules = json.loads(rules_json)
    except Exception:
        return None
    result = {}

    # Extract blocks like {1:...}, {2:...}, etc.
    block_pattern = re.compile(r'\{(\d+):(.*?)\}', re.DOTALL)
    blocks = {m.group(1): m.group(2).strip() for m in block_pattern.finditer(content)}

    # Robust tag extraction
    tag_blocks = parse_swift_tags(content)

    for field, rule in rules.items():
        # Support object rule or string rule
        if isinstance(rule, dict):
            path = rule.get('path')
            condition = rule.get('condition')
            cond_value = rule.get('value')
            multiple = rule.get('multiple', False)
            block_num = rule.get('block')
            postprocess = rule.get('postprocess')
        else:
            path = rule
            condition = None
            cond_value = None
            multiple = False
            block_num = None
            postprocess = None
        value = None
        # Block extraction
        if block_num is not None:
            value = blocks.get(str(block_num), None)
        # Regex extraction
        elif isinstance(path, str) and path.startswith('regex:'):
            pattern = path[len('regex:'):].strip()
            matches = list(re.finditer(pattern, content, re.MULTILINE | re.DOTALL))
            if multiple:
                value = [m.group(1).strip() if m.lastindex else (m.group(0).strip() if m else None) for m in matches]
            else:
                m = matches[0] if matches else None
                value = m.group(1).strip() if m and m.lastindex else (m.group(0).strip() if m else None)
        # Tag extraction
        elif path:
            tag = path if path.startswith(':') else f':{path}:'
            tag_values = tag_blocks.get(tag, None)
            if tag_values:
                if multiple:
                    # Flatten all lines from all occurrences
                    lines = []
                    for val in tag_values:
                        lines.extend([l for l in val.split('\n') if l.strip() != ''])
                    value = lines if lines else None
                else:
                    # Use the first occurrence, join lines
                    value = tag_values[0] if tag_values else None
            else:
                value = None
        # Apply condition if present
        if condition:
            if multiple and isinstance(value, list):
                value = [v for v in value if apply_condition(v, condition, cond_value)]
            else:
                value = apply_condition(value, condition, cond_value)
        # Generic post-processing based on rule['postprocess']
        if postprocess and value:
            func = globals().get(f"process_{postprocess}")
            if callable(func):
                value = func(value)
        result[field] = value
    return result

def extract_xml_fields(content, rules_json):
    import json
    import logging
    import re
    try:
        rules = json.loads(rules_json)
    except Exception:
        return None
    result = {}
    try:
        from lxml import etree
        parser = etree.XMLParser(recover=True)
        # Remove XML declaration if present
        content_no_decl = re.sub(r'<\?xml[^>]*\?>', '', content).strip()
        # Parse as fragments: wrap in a dummy root
        wrapped_content = f'<Root>{content_no_decl}</Root>'
        root = etree.fromstring(wrapped_content.encode('utf-8'), parser=parser)
        nsmap = {}
        apphdr_elem = None
        doc_elem = None
        def get_default_ns_uri(elem):
            return elem.nsmap.get(None)
        # Debug: print tag and nsmap for every element
        for elem in root.iter():
            logging.debug(f"ELEMENT tag: {elem.tag}, nsmap: {elem.nsmap}")
        # Find AppHdr and Document elements and their namespaces robustly
        for elem in root.iter():
            tag_local = etree.QName(elem).localname
            if tag_local == 'AppHdr' and 'app' not in nsmap:
                ns_uri = get_default_ns_uri(elem)
                if ns_uri:
                    nsmap['app'] = ns_uri
                    apphdr_elem = elem
            elif tag_local == 'Document' and 'def' not in nsmap:
                ns_uri = get_default_ns_uri(elem)
                if ns_uri:
                    nsmap['def'] = ns_uri
                    doc_elem = elem
            if 'app' in nsmap and 'def' in nsmap:
                break
        # Fallback: if still not found, search for any AppHdr/Document
        if apphdr_elem is None or 'app' not in nsmap:
            for elem in root.iter():
                if etree.QName(elem).localname == 'AppHdr':
                    ns_uri = get_default_ns_uri(elem)
                    if ns_uri:
                        nsmap['app'] = ns_uri
                    apphdr_elem = elem
                    break
        if doc_elem is None or 'def' not in nsmap:
            for elem in root.iter():
                if etree.QName(elem).localname == 'Document':
                    ns_uri = get_default_ns_uri(elem)
                    if ns_uri:
                        nsmap['def'] = ns_uri
                    doc_elem = elem
                    break
        # If still not found, fallback to first found element
        if apphdr_elem is None:
            for elem in root.iter():
                if etree.QName(elem).localname == 'AppHdr':
                    apphdr_elem = elem
                    break
        if doc_elem is None:
            for elem in root.iter():
                if etree.QName(elem).localname == 'Document':
                    doc_elem = elem
                    break
        logging.debug(f"extract_xml_fields nsmap: {nsmap}")
        logging.debug(f"apphdr_elem tag: {getattr(apphdr_elem, 'tag', None)}")
        logging.debug(f"doc_elem tag: {getattr(doc_elem, 'tag', None)}")
        def extract_field(rule, context=None):
            if isinstance(rule, dict):
                path = rule.get('path')
                condition = rule.get('condition')
                cond_value = rule.get('value')
                multiple = rule.get('multiple', False)
                fields = rule.get('fields')
            else:
                path = rule
                condition = None
                cond_value = None
                multiple = False
                fields = None
            value = None
            if path:
                xp = path
                if xp.startswith('/def:Document'):
                    base = doc_elem
                    xp = '.' + xp[len('/def:Document'):]
                elif xp.startswith('/app:AppHdr'):
                    base = apphdr_elem
                    xp = '.' + xp[len('/app:AppHdr'):]
                else:
                    base = context if context is not None else root
                logging.debug(f"extract_field: path={xp}, base_tag={getattr(base, 'tag', None)}")
                try:
                    found = base.xpath(xp, namespaces=nsmap) if hasattr(base, 'xpath') else []
                    logging.debug(f"extract_field: found={found}")
                    if fields:
                        if multiple:
                            value = []
                            for elem in found:
                                obj = {}
                                for subfield, subrule in fields.items():
                                    obj[subfield] = extract_field(subrule, context=elem)
                                value.append(obj)
                        else:
                            elem = found[0] if found else None
                            if elem is not None:
                                obj = {}
                                for subfield, subrule in fields.items():
                                    obj[subfield] = extract_field(subrule, context=elem)
                                value = obj
                            else:
                                value = None
                    else:
                        if multiple:
                            value = []
                            for elem in found:
                                if isinstance(elem, etree._Element):
                                    v = elem.text
                                else:
                                    v = str(elem)
                                if condition:
                                    v = apply_condition(v, condition, cond_value)
                                value.append(v)
                            value = [v for v in value if v is not None]
                        else:
                            elem = found[0] if found else None
                            if isinstance(elem, etree._Element):
                                value = elem.text
                            elif elem is not None:
                                value = str(elem)
                            else:
                                value = None
                            if condition:
                                value = apply_condition(value, condition, cond_value)
                except Exception as e:
                    logging.debug(f"extract_field: Exception {e}")
                    value = None
            return value
        for field, rule in rules.items():
            result[field] = extract_field(rule)
    except Exception as e:
        logging.debug(f"extract_xml_fields: Exception {e}")
        return None
    return result

@config.route('/config/auditlog/<int:config_id>')
@login_required
@admin_required
def config_auditlog(config_id):
    config_obj = Configuration.query.get_or_404(config_id)
    # Filter audit logs for this configuration (by name and filetype)
    logs = AuditLog.query.filter(
        AuditLog.filetype == config_obj.file_type,
        AuditLog.details.ilike(f"%{config_obj.name}%")
    ).order_by(AuditLog.timestamp.desc()).all()  # DESC order

    # Fetch all versions of the configuration (by audit log order)
    import re
    config_versions = []
    for log in logs:
        # Use regex to extract rules and schema
        rules = None
        schema = None
        rules_match = re.search(r'rules:(.*?)schema:', log.details, re.DOTALL)
        schema_match = re.search(r'schema:(.*)', log.details, re.DOTALL)
        if rules_match:
            rules = rules_match.group(1).strip()
        if schema_match:
            schema = schema_match.group(1).strip()
        config_versions.append({'rules': rules, 'schema': schema, 'log': log})

    # Compute diffs for rules and schema between versions (descending order)
    diffs = []
    html_diff = difflib.HtmlDiff(wrapcolumn=80)
    for i in range(len(config_versions) - 1):
        curr = config_versions[i]
        prev = config_versions[i+1]
        rules_side_by_side = None
        schema_side_by_side = None
        if prev['rules'] and curr['rules']:
            rules_side_by_side = html_diff.make_table(
                prev['rules'].splitlines(),
                curr['rules'].splitlines(),
                fromdesc='Previous',
                todesc='Current',
                context=True, numlines=3)
        if prev['schema'] and curr['schema']:
            schema_side_by_side = html_diff.make_table(
                prev['schema'].splitlines(),
                curr['schema'].splitlines(),
                fromdesc='Previous',
                todesc='Current',
                context=True, numlines=3)
        diffs.append({'log': curr['log'],
                      'rules_side_by_side': rules_side_by_side,
                      'schema_side_by_side': schema_side_by_side})

    # No need to reverse diffs; logs are already in DESC order

    # Pass info about missing rules/schema for each log
    logs_with_info = []
    for idx, log in enumerate(logs):
        rules_present = 'rules:' in log.details
        schema_present = 'schema:' in log.details
        logs_with_info.append({'log': log, 'rules_present': rules_present, 'schema_present': schema_present, 'index': idx})

    return render_template('config_auditlog.html', config=config_obj, logs=logs_with_info, diffs=diffs)

# Export audit logs as CSV for a configuration
@config.route('/config/auditlog/export/<int:config_id>')
@login_required
@admin_required
def export_config_auditlog(config_id):
    config_obj = Configuration.query.get_or_404(config_id)
    logs = AuditLog.query.filter(
        AuditLog.filetype == config_obj.file_type,
        AuditLog.details.ilike(f"%{config_obj.name}%")
    ).order_by(AuditLog.timestamp.asc()).all()
    def generate():
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Timestamp', 'User', 'Action', 'Details'])
        for log in logs:
            writer.writerow([log.timestamp, log.user, log.action, log.details])
        return output.getvalue()
    return Response(generate(), mimetype='text/csv', headers={'Content-Disposition': 'attachment;filename=auditlog.csv'})

@config.app_errorhandler(403)
def forbidden(e):
    g.error_403 = 'You do not have permission to access this page. Only admins are allowed.'
    return render_template('config.html', configs=[]), 403

filetypes = Blueprint('filetypes', __name__)

@filetypes.route('/filetypes')
@login_required
@admin_required
def list_filetypes():
    search = request.args.get('search', '').strip()
    query = FileType.query
    if search:
        query = query.filter(FileType.name.ilike(f'%{search}%'))
    filetypes = query.order_by(FileType.name).all()
    from ..models import Configuration
    import os
    from flask import current_app, url_for
    # Annotate each filetype with usage_count and template status
    TEMPLATE_DIR = os.path.join(current_app.root_path, 'templates', 'filetypes')
    for ft in filetypes:
        ft.usage_count = Configuration.query.filter_by(file_type=ft.name).count()
        # Check for .xml.j2 and .txt.j2 templates (add more extensions as needed)
        for ext in ['xml', 'txt']:
            template_path = os.path.join(TEMPLATE_DIR, f'{ft.name}.{ext}.j2')
            if os.path.exists(template_path):
                ft.has_template = True
                ft.template_url = url_for('static', filename=f'filetypes/{ft.name}.{ext}.j2')
                break
        else:
            ft.has_template = False
            ft.template_url = None
    return render_template('filetypes.html', filetypes=filetypes, errors=[], search=search)

@filetypes.route('/filetypes/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_filetype():
    errors = []
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        extraction_rules = request.form.get('extraction_rules', '{}')
        file_mode = request.form.get('file_mode', 'text').strip().lower()
        if not name:
            errors.append('File type name is required.')
        if len(name) > 100:
            errors.append('File type name must be at most 100 characters.')
        if len(description) > 255:
            errors.append('Description must be at most 255 characters.')
        if FileType.query.filter_by(name=name).first():
            errors.append('File type already exists.')
        if errors:
            for e in errors:
                flash(e)
            return render_template('filetype_form.html', errors=errors)
        ft = FileType(name=name, description=description, active=True, extraction_rules=extraction_rules, file_mode=file_mode)
        db.session.add(ft)
        db.session.commit()
        # Audit log
        db.session.add(AuditLog(user=current_user.username, action='add', filetype=name, details=f'Added file type: {name}'))
        db.session.commit()
        flash('File type added successfully!')
        return redirect(url_for('filetypes.list_filetypes'))
    return render_template('filetype_form.html', errors=errors)

@filetypes.route('/filetypes/delete/<int:filetype_id>', methods=['POST'])
@login_required
@admin_required
def delete_filetype(filetype_id):
    ft = FileType.query.get_or_404(filetype_id)
    # Prevent deletion if used in any configuration
    from ..models import Configuration
    if Configuration.query.filter_by(file_type=ft.name).first():
        flash('Cannot delete file type: it is used in a configuration.')
        return redirect(url_for('filetypes.list_filetypes'))
    db.session.delete(ft)
    db.session.commit()
    # Audit log
    db.session.add(AuditLog(user=current_user.username, action='delete', filetype=ft.name, details=f'Deleted file type: {ft.name}'))
    db.session.commit()
    flash('File type deleted successfully!')
    return redirect(url_for('filetypes.list_filetypes'))

@filetypes.route('/filetypes/edit/<int:filetype_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_filetype(filetype_id):
    ft = FileType.query.get_or_404(filetype_id)
    errors = []
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        extraction_rules = request.form.get('extraction_rules', '{}')
        file_mode = request.form.get('file_mode', 'text').strip().lower()
        if not name:
            errors.append('File type name is required.')
        if len(name) > 100:
            errors.append('File type name must be at most 100 characters.')
        if len(description) > 255:
            errors.append('Description must be at most 255 characters.')
        if FileType.query.filter(FileType.name == name, FileType.id != filetype_id).first():
            errors.append('Another file type with this name already exists.')
        if errors:
            for e in errors:
                flash(e)
            return render_template('filetype_form.html', filetype=ft, errors=errors)
        old_name = ft.name
        old_desc = ft.description
        ft.name = name
        ft.description = description
        ft.extraction_rules = extraction_rules
        ft.file_mode = file_mode
        db.session.commit()
        # Audit log
        db.session.add(AuditLog(user=current_user.username, action='edit', filetype=name, details=f'Edited file type: {old_name} -> {name}, {old_desc} -> {description}'))
        db.session.commit()
        flash('File type updated successfully!')
        return redirect(url_for('filetypes.list_filetypes'))
    return render_template('filetype_form.html', filetype=ft, errors=errors)

@filetypes.route('/filetypes/toggle/<int:filetype_id>', methods=['POST'])
@login_required
@admin_required
def toggle_filetype(filetype_id):
    ft = FileType.query.get_or_404(filetype_id)
    ft.active = not ft.active
    db.session.commit()
    # Audit log
    db.session.add(AuditLog(user=current_user.username, action='toggle', filetype=ft.name, details=f'Toggled file type: {ft.name} to {"active" if ft.active else "inactive"}'))
    db.session.commit()
    flash(f'File type {"activated" if ft.active else "deactivated"}!')
    return redirect(url_for('filetypes.list_filetypes'))

@filetypes.route('/filetypes/auditlog')
@login_required
@admin_required
def auditlog():
    query = AuditLog.query
    username = request.args.get('username', '').strip()
    action = request.args.get('action', '').strip()
    filetype = request.args.get('filetype', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    if username:
        query = query.filter(AuditLog.user.ilike(f'%{username}%'))
    if action:
        query = query.filter(AuditLog.action.ilike(f'%{action}%'))
    if filetype:
        query = query.filter(AuditLog.filetype.ilike(f'%{filetype}%'))
    if date_from:
        from datetime import datetime
        try:
            dt_from = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(AuditLog.timestamp >= dt_from)
        except Exception:
            pass
    if date_to:
        from datetime import datetime, timedelta
        try:
            dt_to = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(AuditLog.timestamp < dt_to)
        except Exception:
            pass
    logs = query.order_by(AuditLog.timestamp.desc()).limit(100).all()
    return render_template('filetype_auditlog.html', logs=logs, username=username, action=action, filetype=filetype, date_from=date_from, date_to=date_to)

def diff_highlight(diff_text):
    lines = diff_text.splitlines()
    html = []
    for line in lines:
        if line.startswith('+') and not line.startswith('+++'):
            html.append(f'<span class="diff-add">{line}</span>')
        elif line.startswith('-') and not line.startswith('---'):
            html.append(f'<span class="diff-del">{line}</span>')
        elif line.startswith('@@'):
            html.append(f'<span class="diff-hdr">{line}</span>')
        elif line.startswith('+++') or line.startswith('---'):
            html.append(f'<span class="diff-hdr">{line}</span>')
        else:
            html.append(f'<span class="diff-ctx">{line}</span>')
    return Markup('\n'.join(html))

def init_app(app):
    app.jinja_env.filters['diff_highlight'] = diff_highlight 

# --- Backfill script for AuditLog entries ---
@config.route('/config/backfill_auditlog')
@login_required
@admin_required
def backfill_auditlog():
    configs = Configuration.query.all()
    updated = 0
    for config in configs:
        logs = AuditLog.query.filter(
            AuditLog.filetype == config.file_type,
            AuditLog.details.ilike(f"%{config.name}%")
        ).all()
        for log in logs:
            # Only update if rules/schema are missing
            if 'rules:' not in log.details or 'schema:' not in log.details:
                rules_pretty = json.dumps(json.loads(config.rules), indent=2, sort_keys=True) if config.rules else ''
                schema_pretty = json.dumps(json.loads(config.schema), indent=2, sort_keys=True) if config.schema else ''
                log.details = f"{log.details}\nrules:{rules_pretty}\nschema:{schema_pretty}"
                updated += 1
    db.session.commit()
    flash(f'Backfilled {updated} audit log entries with rules and schema.')
    return redirect(url_for('config.configuration'))

# --- Blueprint for converter configs ---
converters = Blueprint('converters', __name__)

@converters.route('/config/converters')
@login_required
@admin_required
def list_converters():
    configs = ConverterConfig.query.all()
    return render_template('converter_configs.html', configs=configs)

@converters.route('/config/converters/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_converter():
    if request.method == 'POST':
        # Validate JSON
        try:
            import json
            json.loads(request.form.get('rules', '{}'))
        except Exception:
            flash('Rules must be valid JSON.')
            return render_template('converter_config_form.html', action='Add')
        if request.form.get('schema'):
            try:
                json.loads(request.form.get('schema'))
            except Exception:
                flash('Schema must be valid JSON.')
                return render_template('converter_config_form.html', action='Add')
        config = ConverterConfig(
            name=request.form.get('name'),
            description=request.form.get('description'),
            source_type=request.form.get('source_type'),
            target_type=request.form.get('target_type'),
            rules=request.form.get('rules'),
            schema=request.form.get('schema')
        )
        db.session.add(config)
        db.session.commit()
        flash('Converter configuration added successfully!')
        return redirect(url_for('converters.list_converters'))
    return render_template('converter_config_form.html', action='Add')

@converters.route('/config/converters/edit/<int:config_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_converter(config_id):
    config = ConverterConfig.query.get_or_404(config_id)
    if request.method == 'POST':
        try:
            import json
            json.loads(request.form.get('rules', '{}'))
        except Exception:
            flash('Rules must be valid JSON.')
            return render_template('converter_config_form.html', action='Edit', config=config)
        if request.form.get('schema'):
            try:
                json.loads(request.form.get('schema'))
            except Exception:
                flash('Schema must be valid JSON.')
                return render_template('converter_config_form.html', action='Edit', config=config)
        config.name = request.form.get('name')
        config.description = request.form.get('description')
        config.source_type = request.form.get('source_type')
        config.target_type = request.form.get('target_type')
        config.rules = request.form.get('rules')
        config.schema = request.form.get('schema')
        print("Saving rules:", config.rules)
        db.session.commit()
        print("Saved config:", config.rules)
        flash('Converter configuration updated successfully!')
        return redirect(url_for('converters.list_converters'))
    # Pre-populate form fields for GET
    return render_template('converter_config_form.html', action='Edit', config=config)

@converters.route('/config/converters/delete/<int:config_id>', methods=['POST'])
@login_required
@admin_required
def delete_converter(config_id):
    config = ConverterConfig.query.get_or_404(config_id)
    db.session.delete(config)
    db.session.commit()
    flash('Converter configuration deleted successfully!')
    return redirect(url_for('converters.list_converters'))

@converters.route('/test-workflow', methods=['GET'])
@login_required
@admin_required
def test_workflow():
    workflows = Workflow.query.order_by(Workflow.created_at.desc()).all()
    converter_configs = ConverterConfig.query.all()
    return render_template('test_workflow.html', workflows=workflows, converter_configs=converter_configs)

@converters.route('/test-workflow/create', methods=['POST'])
@login_required
@admin_required
def create_workflow():
    import json
    name = request.form.get('workflow_name', '').strip()
    stages = request.form.getlist('stages[]')
    if not name or not stages:
        flash('Workflow name and at least one stage are required.', 'danger')
        return redirect(url_for('converters.test_workflow'))
    workflow = Workflow(name=name, stages=json.dumps(stages))
    db.session.add(workflow)
    db.session.commit()
    flash('Workflow created successfully!', 'success')
    return redirect(url_for('converters.test_workflow'))

@converters.route('/test-workflow/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_workflow(id):
    workflow = Workflow.query.get_or_404(id)
    db.session.delete(workflow)
    db.session.commit()
    flash('Workflow deleted.', 'success')
    return redirect(url_for('converters.test_workflow'))

@converters.route('/test-workflow/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_workflow(id):
    # Stub for now
    flash('Edit workflow not implemented yet.', 'info')
    return redirect(url_for('converters.test_workflow'))

@converters.route('/test-workflow/<int:id>/execute', methods=['GET', 'POST'])
@login_required
@admin_required
def execute_workflow(id):
    import json, os, tempfile
    from flask import session, request
    workflow = Workflow.query.get_or_404(id)
    stages = json.loads(workflow.stages)
    converter_configs = {str(cfg.id): cfg for cfg in ConverterConfig.query.all()}
    session_key = f'workflow_{id}_stage'
    input_key = f'workflow_{id}_input'
    files_key = f'workflow_{id}_stage_files'
    # Step 1: Upload initial input file if not present
    if input_key not in session:
        if request.method == 'POST' and 'initial_input' in request.files:
            file = request.files['initial_input']
            if file and file.filename:
                content = file.read().decode('utf-8')
                session[input_key] = content
                session[session_key] = 0
                session[files_key] = {}
        if input_key not in session:
            return render_template('test_workflow_execute.html', workflow=workflow, stages=stages, converter_configs=converter_configs, stage_idx=None, need_input=True)
    # Workflow execution
    if request.method == 'POST' and 'reset_workflow' in request.form:
        session.pop(input_key, None)
        session.pop(session_key, None)
        session.pop(files_key, None)
        return render_template('test_workflow_execute.html', workflow=workflow, stages=stages, converter_configs=converter_configs, stage_idx=None, need_input=True)
    if files_key not in session:
        session[files_key] = {}
    if request.method == 'POST' and 'action' in request.form:
        action = request.form.get('action')
        if action == 'pass':
            session[session_key] = session.get(session_key, 0) + 1
            # Clear actual file for next stage
            session[files_key][str(session[session_key])] = None
        elif action == 'fail':
            session[session_key] = -1
    stage_idx = session.get(session_key, 0)
    if stage_idx == -1:
        # On fail, clear session for this workflow
        session.pop(input_key, None)
        session.pop(session_key, None)
        session.pop(files_key, None)
        return render_template('test_workflow_execute.html', workflow=workflow, stages=stages, converter_configs=converter_configs, stage_idx=stage_idx, done=True, failed=True)
    if stage_idx >= len(stages):
        session.pop(input_key, None)
        session.pop(session_key, None)
        session.pop(files_key, None)
        return render_template('test_workflow_execute.html', workflow=workflow, stages=stages, converter_configs=converter_configs, stage_idx=stage_idx, done=True, failed=False)
    # Current stage
    stage_cfg_id = stages[stage_idx]
    stage_cfg = converter_configs.get(str(stage_cfg_id))
    expected_output = None
    html_diff = None
    actual_content = session[files_key].get(str(stage_idx))
    error = None
    prev_output = session[input_key]
    # Generate expected output for this stage
    if stage_cfg:
        import re, json
        template_dir = os.path.join(current_app.root_path, 'templates', 'filetypes')
        template_content = None
        for ext in ['xml', 'txt']:
            template_path = os.path.join(template_dir, f'{stage_cfg.target_type}.{ext}.j2')
            if os.path.exists(template_path):
                with open(template_path, encoding='utf-8') as f:
                    template_content = f.read()
                break
        if template_content:
            try:
                mapping_rules = json.loads(stage_cfg.rules)
            except Exception as e:
                error = f"Error in mapping: {e}"
                mapping_rules = {}
            from ..models import FileType
            source_filetype = FileType.query.filter_by(name=stage_cfg.source_type).first()
            extraction_rules = source_filetype.extraction_rules if source_filetype else '{}'
            if source_filetype and source_filetype.file_mode == 'xml':
                extracted = extract_xml_with_xpaths(prev_output, extraction_rules)
            else:
                extracted = extract_generic_text_fields(prev_output, template_content)
            mapped_data = {}
            for tgt_var in re.findall(r'@@(.*?)@@', template_content):
                map_cfg = mapping_rules.get(tgt_var, {}) if isinstance(mapping_rules.get(tgt_var), dict) else {}
                value = ''
                if map_cfg.get('sources') and map_cfg.get('transform'):
                    sources = map_cfg['sources']
                    vals = [extracted.get(s, '') for s in sources]
                    transform_func = globals().get(map_cfg['transform'])
                    if callable(transform_func):
                        value = transform_func(vals)
                    else:
                        value = ''.join(vals)
                elif map_cfg.get('source'):
                    value = extracted.get(map_cfg['source'], map_cfg.get('default', ''))
                elif 'default' in map_cfg:
                    value = map_cfg['default']
                else:
                    value = ''
                if value and map_cfg.get('prefix'):
                    value = f"{map_cfg['prefix']}{value}"
                mapped_data[tgt_var] = value if value is not None else ''
            def replace_vars(match):
                var = match.group(1)
                return str(mapped_data.get(var, ''))
            expected_output = re.sub(r'@@(.*?)@@', replace_vars, template_content)
    # Handle actual file upload and diff
    if request.method == 'POST' and 'actual_file' in request.files and actual_content is None:
        file = request.files['actual_file']
        if file and file.filename:
            actual_content = file.read().decode('utf-8')
            # Side-by-side HTML diff
            import difflib
            html_diff = difflib.HtmlDiff(wrapcolumn=80).make_table(
                expected_output.splitlines(),
                actual_content.splitlines(),
                fromdesc='Expected Output',
                todesc='Actual Uploaded File',
                context=True, numlines=3
            )
            # Store actual file for this stage
            session[files_key][str(stage_idx)] = actual_content
            session.modified = True
            # Store expected output as next input for next stage if passed
            # (done in Pass action)
    # If actual_content is present, generate diff
    if actual_content and html_diff is None and expected_output:
        import difflib
        html_diff = difflib.HtmlDiff(wrapcolumn=80).make_table(
            expected_output.splitlines(),
            actual_content.splitlines(),
            fromdesc='Expected Output',
            todesc='Actual Uploaded File',
            context=True, numlines=3
        )
    return render_template('test_workflow_execute.html', workflow=workflow, stages=stages, converter_configs=converter_configs, stage_idx=stage_idx, stage_cfg=stage_cfg, expected_output=expected_output, actual_content=actual_content, html_diff=html_diff, error=error, done=False, failed=False, need_input=False)

@converters.route('/test-workflow/<int:id>/audit', methods=['GET'])
@login_required
@admin_required
def audit_workflow(id):
    # Stub for now
    flash('Audit log not implemented yet.', 'info')
    return redirect(url_for('converters.test_workflow'))

@converters.route('/data-generator', methods=['GET', 'POST'])
@login_required
@admin_required
def data_generator():
    import os, json, tempfile
    from flask import request, render_template, send_file, url_for, current_app
    from ..models import FileType
    filetypes = [ft.name for ft in FileType.query.order_by(FileType.name).all()]
    selected_type = request.form.get('file_type') if request.method == 'POST' else None
    template_vars = []
    generated_file = None
    download_url = None
    values = {}
    if selected_type:
        # Get template variables
        template_dir = os.path.join(current_app.root_path, 'templates', 'filetypes')
        template_content = None
        file_ext = None
        for ext in ['xml', 'txt']:
            template_path = os.path.join(template_dir, f'{selected_type}.{ext}.j2')
            if os.path.exists(template_path):
                with open(template_path, encoding='utf-8') as f:
                    template_content = f.read()
                file_ext = ext
                break
        if template_content:
            import re
            template_vars = re.findall(r'@@(.*?)@@', template_content)
            if request.method == 'POST':
                # Collect values for each variable
                values = {var: request.form.get(var, '') for var in template_vars}
                # Render template
                def replace_vars(match):
                    var = match.group(1)
                    return str(values.get(var, ''))
                rendered_output = re.sub(r'@@(.*?)@@', replace_vars, template_content)
                # Save to temp file and provide download
                temp_dir = tempfile.gettempdir()
                temp_filename = f'generated_{selected_type}.{file_ext}'
                temp_path = os.path.join(temp_dir, temp_filename)
                with open(temp_path, 'w', encoding='utf-8') as f:
                    f.write(rendered_output)
                download_url = url_for('converters.download_generated', filename=temp_filename)
    return render_template('data_generator.html', filetypes=filetypes, selected_type=selected_type, template_vars=template_vars, values=values, download_url=download_url)

@converters.route('/data-generator/download/<filename>')
@login_required
@admin_required
def download_generated(filename):
    import tempfile, os
    temp_dir = tempfile.gettempdir()
    return send_file(os.path.join(temp_dir, filename), as_attachment=True)

@converters.route('/converters/test', methods=['GET', 'POST'])
@login_required
@admin_required
def converter_test():
    converter_configs = ConverterConfig.query.all()
    def converter_to_dict(c):
        return {
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "source_type": c.source_type,
            "target_type": c.target_type
        }
    converter_configs_dict = [converter_to_dict(c) for c in converter_configs]
    result = None
    error = None
    download_url = None
    selected_id = request.form.get('converter_id')
    if request.method == 'POST' and selected_id:
        converter = ConverterConfig.query.get(int(selected_id))
        if not converter:
            error = "Converter config not found."
        else:
            file = request.files.get('source_file')
            if not file or file.filename == '':
                error = "Please upload a file."
            else:
                content = file.read().decode('utf-8')
                import re, json, os
                template_dir = os.path.join(current_app.root_path, 'templates', 'filetypes')
                template_content = None
                file_ext = None
                for ext in ['xml', 'txt']:
                    template_path = os.path.join(template_dir, f'{converter.target_type}.{ext}.j2')
                    if os.path.exists(template_path):
                        with open(template_path, encoding='utf-8') as f:
                            template_content = f.read()
                        file_ext = ext
                        break
                if not template_content:
                    error = "No template found for target type."
                    result = None
                    download_url = None
                else:
                    try:
                        mapping_rules = json.loads(converter.rules)
                    except Exception as e:
                        error = f"Error in mapping: {e}"
                        mapping_rules = {}
                    # --- Use extraction_rules from source file type for extraction ---
                    from ..models import FileType
                    source_filetype = FileType.query.filter_by(name=converter.source_type).first()
                    extraction_rules = source_filetype.extraction_rules if source_filetype else '{}'
                    if source_filetype and source_filetype.file_mode == 'xml':
                        extracted = extract_xml_with_xpaths(content, extraction_rules)
                    else:
                        extracted = extract_generic_text_fields(content, template_content)
                    print('Extracted variables:', extracted)
                    mapped_data = {}
                    for tgt_var in re.findall(r'@@(.*?)@@', template_content):
                        map_cfg = mapping_rules.get(tgt_var, {}) if isinstance(mapping_rules.get(tgt_var), dict) else {}
                        # --- Enhanced mapping logic ---
                        value = ''
                        if map_cfg.get('sources') and map_cfg.get('transform'):
                            # Composite field with transform
                            sources = map_cfg['sources']
                            vals = [extracted.get(s, '') for s in sources]
                            transform_func = globals().get(map_cfg['transform'])
                            if callable(transform_func):
                                value = transform_func(vals)
                            else:
                                value = ''.join(vals)
                        elif map_cfg.get('source'):
                            value = extracted.get(map_cfg['source'], map_cfg.get('default', ''))
                        elif 'default' in map_cfg:
                            value = map_cfg['default']
                        else:
                            value = ''
                        # Apply prefix if specified
                        if value and map_cfg.get('prefix'):
                            value = f"{map_cfg['prefix']}{value}"
                        # Apply transformation if specified (uppercase, lowercase, date_format)
                        transform = map_cfg.get('transform', 'none')
                        date_format = map_cfg.get('date_format', '')
                        if value is not None and value != '':
                            if transform == 'uppercase':
                                value = str(value).upper()
                            elif transform == 'lowercase':
                                value = str(value).lower()
                            elif transform == 'date_format' and date_format:
                                import datetime
                                try:
                                    dt = None
                                    for fmt in ('%Y-%m-%d', '%Y%m%d', '%d-%m-%Y', '%Y/%m/%d'):
                                        try:
                                            dt = datetime.datetime.strptime(str(value), fmt)
                                            break
                                        except Exception:
                                            continue
                                    if dt:
                                        value = dt.strftime(date_format)
                                except Exception:
                                    pass
                        mapped_data[tgt_var] = value if value is not None else ''
                    def replace_vars(match):
                        var = match.group(1)
                        return str(mapped_data.get(var, ''))
                    rendered_output = re.sub(r'@@(.*?)@@', replace_vars, template_content)
                    result = rendered_output
                    temp_dir = tempfile.gettempdir()
                    temp_filename = f'converted_output.{file_ext}'
                    temp_path = os.path.join(temp_dir, temp_filename)
                    with open(temp_path, 'w', encoding='utf-8') as f:
                        f.write(rendered_output)
                    download_url = url_for('converters.download_generated', filename=temp_filename)
    return render_template('converter_test.html', converter_configs=converter_configs, converter_configs_dict=converter_configs_dict, result=result, error=error, download_url=download_url)

def extract_generic_text_fields(file_content, template_content=None):
    import re
    tag_dict = {}
    current_tag = None
    current_value_lines = []
    # Normalize line endings
    lines = file_content.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    for line in lines:
        # End of block marker
        if line.strip() == '-}':
            break
        # Tag detection
        tag_match = re.match(r'^\s*(:[0-9A-Za-z]{2,3}:)', line)
        if tag_match:
            # Save previous tag's value
            if current_tag is not None:
                tag_dict[current_tag] = list(current_value_lines)
            # Start new tag
            current_tag = tag_match.group(1)[1:-1]  # e.g., '50K'
            value = line[line.find(tag_match.group(1)) + len(tag_match.group(1)):]
            current_value_lines = [value] if value.strip() or value == '' else []
        elif current_tag is not None:
            current_value_lines.append(line)
    # Save last tag
    if current_tag is not None:
        tag_dict[current_tag] = list(current_value_lines)
    # Flatten for output
    tags = {}
    for tag, lines in tag_dict.items():
        tags[f'tag{tag}'] = ' '.join([l.strip() for l in lines])
        for idx, line in enumerate(lines):
            tags[f'tag{tag}Line{idx+1}'] = line.strip()
    return tags

def extract_xml_with_xpaths(file_content, rules_json):
    import json
    from lxml import etree
    import re
    rules = json.loads(rules_json)
    # Strip namespaces
    def strip_ns(xml):
        xml = re.sub(r'xmlns(:\w+)?="[^"]*"', '', xml)
        xml = re.sub(r'<(/?)(\w+):', r'<\1', xml)
        xml = re.sub(r'(</?)(\w+):', r'\1', xml)
        return xml
    file_content = strip_ns(file_content)
    content_no_decl = re.sub(r'<\?xml[^>]*\?>', '', file_content).strip()
    wrapped_content = f'<Root>{content_no_decl}</Root>'
    root = etree.fromstring(wrapped_content.encode('utf-8'), parser=etree.XMLParser(recover=True))
    result = {}
    for var, xpath in rules.items():
        try:
            found = root.xpath(xpath)
            if found:
                if isinstance(found[0], etree._Element):
                    result[var] = (found[0].text or '').strip()
                else:
                    result[var] = str(found[0]).strip()
            else:
                result[var] = ''
        except Exception as e:
            result[var] = ''
    return result