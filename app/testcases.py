from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response, abort
from flask_login import login_required, current_user
from .models import TestCase, TestRun, Workflow, AuditLog, TestCaseWorkflow
from . import db
from datetime import datetime, timedelta
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SelectMultipleField, SubmitField, FileField, FieldList
from wtforms.validators import DataRequired, Optional
from sqlalchemy.orm import joinedload
import random
import csv
from functools import wraps
from flask_wtf.file import FileAllowed, FileRequired
import os

# Blueprint definition

testcases = Blueprint('testcases', __name__)

class TestCaseForm(FlaskForm):
    name = StringField('Test Case Name', validators=[DataRequired()])
    workflows = SelectMultipleField('Workflows', coerce=int)
    description = StringField('Description', validators=[Optional()])
    schedule = SelectField('Schedule', choices=[('none', 'None'), ('daily', 'Daily'), ('weekly', 'Weekly')], default='none')
    submit = SubmitField('Save')

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def permission_required(permission_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            if not current_user.role or not any(p.name == permission_name for p in current_user.role.permissions):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@testcases.route('/testcases', methods=['GET'])
@login_required
def list_testcases():
    testcases = TestCase.query.order_by(TestCase.created_at.desc()).all()
    workflows = {w.id: w for w in Workflow.query.all()}
    return render_template('testcases.html', testcases=testcases, workflows=workflows)

@testcases.route('/testcases/new', methods=['GET', 'POST'])
@login_required
@permission_required('testcase_create')
def create_testcase():
    form = TestCaseForm()
    form.workflows.choices = [(w.id, w.name) for w in Workflow.query.order_by(Workflow.name).all()]
    if form.validate_on_submit():
        # Custom validation for dynamic workflows
        workflow_ids = []
        i = 0
        while True:
            wf_key = f'workflow_{i}'
            if wf_key not in request.form:
                break
            wf_id = request.form.get(wf_key)
            if wf_id:
                workflow_ids.append(wf_id)
            i += 1
        if not workflow_ids:
            flash('At least one workflow must be added.', 'danger')
            return render_template('testcase_form.html', form=form, action='Create')
        if len(set(workflow_ids)) != len(workflow_ids):
            flash('Duplicate workflows are not allowed.', 'danger')
            return render_template('testcase_form.html', form=form, action='Create')
        testcase = TestCase(
            name=form.name.data,
            description=form.description.data,
            schedule=form.schedule.data if form.schedule.data != 'none' else None,
            next_run_at=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(testcase)
        db.session.flush()  # Get testcase.id
        # Ensure uploads directory exists
        os.makedirs('uploads', exist_ok=True)
        # Handle dynamic workflow associations and file uploads
        i = 0
        while True:
            wf_key = f'workflow_{i}'
            file_key = f'sample_file_{i}'
            if wf_key not in request.form:
                break
            wf_id = request.form.get(wf_key)
            if not wf_id:
                i += 1
                continue
            file_field = request.files.get(file_key)
            sample_file_path = None
            if file_field and file_field.filename:
                filename = f"testcase_{testcase.id}_workflow_{wf_id}_" + file_field.filename
                file_path = f"uploads/{filename}"
                file_field.save(file_path)
                sample_file_path = file_path
            assoc = TestCaseWorkflow(test_case_id=testcase.id, workflow_id=int(wf_id), sample_file=sample_file_path)
            db.session.add(assoc)
            i += 1
        db.session.commit()
        db.session.add(AuditLog(
            user=current_user.username,
            action='create',
            filetype='testcase',
            details=f"Created test case: {testcase.name} (ID: {testcase.id})"
        ))
        db.session.commit()
        flash('Test case created successfully!', 'success')
        return redirect(url_for('testcases.list_testcases'))
    return render_template('testcase_form.html', form=form, action='Create')

@testcases.route('/testcases/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('testcase_edit')
def edit_testcase(id):
    testcase = TestCase.query.get_or_404(id)
    form = TestCaseForm(obj=testcase)
    form.workflows.choices = [(w.id, w.name) for w in Workflow.query.order_by(Workflow.name).all()]
    if request.method == 'GET':
        form.workflows.data = [assoc.workflow_id for assoc in testcase.workflows_assoc]
        form.schedule.data = testcase.schedule or 'none'
    if form.validate_on_submit():
        # Custom validation for dynamic workflows
        workflow_ids = []
        i = 0
        while True:
            wf_key = f'workflow_{i}'
            if wf_key not in request.form:
                break
            wf_id = request.form.get(wf_key)
            if wf_id:
                workflow_ids.append(wf_id)
            i += 1
        if not workflow_ids:
            flash('At least one workflow must be added.', 'danger')
            return render_template('testcase_form.html', form=form, action='Edit')
        if len(set(workflow_ids)) != len(workflow_ids):
            flash('Duplicate workflows are not allowed.', 'danger')
            return render_template('testcase_form.html', form=form, action='Edit')
        testcase.name = form.name.data
        testcase.description = form.description.data
        testcase.schedule = form.schedule.data if form.schedule.data != 'none' else None
        testcase.updated_at = datetime.utcnow()
        # Remove old associations
        TestCaseWorkflow.query.filter_by(test_case_id=testcase.id).delete()
        # Ensure uploads directory exists
        os.makedirs('uploads', exist_ok=True)
        # Add new associations and handle file uploads
        i = 0
        while True:
            wf_key = f'workflow_{i}'
            file_key = f'sample_file_{i}'
            if wf_key not in request.form:
                break
            wf_id = request.form.get(wf_key)
            if not wf_id:
                i += 1
                continue
            file_field = request.files.get(file_key)
            sample_file_path = None
            if file_field and file_field.filename:
                filename = f"testcase_{testcase.id}_workflow_{wf_id}_" + file_field.filename
                file_path = f"uploads/{filename}"
                file_field.save(file_path)
                sample_file_path = file_path
            assoc = TestCaseWorkflow(test_case_id=testcase.id, workflow_id=int(wf_id), sample_file=sample_file_path)
            db.session.add(assoc)
            i += 1
        db.session.commit()
        db.session.add(AuditLog(
            user=current_user.username,
            action='edit',
            filetype='testcase',
            details=f"Edited test case: {testcase.name} (ID: {testcase.id})"
        ))
        db.session.commit()
        flash('Test case updated successfully!', 'success')
        return redirect(url_for('testcases.list_testcases'))
    return render_template('testcase_form.html', form=form, action='Edit')

@testcases.route('/testcases/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('testcase_delete')
def delete_testcase(id):
    testcase = TestCase.query.get_or_404(id)
    # Delete all associated test runs
    TestRun.query.filter_by(test_case_id=testcase.id).delete()
    db.session.delete(testcase)
    db.session.commit()
    db.session.add(AuditLog(
        user=current_user.username,
        action='delete',
        filetype='testcase',
        details=f"Deleted test case: {testcase.name} (ID: {testcase.id})"
    ))
    db.session.commit()
    flash('Test case deleted successfully!', 'success')
    return redirect(url_for('testcases.list_testcases'))

@testcases.route('/testcases/execute', methods=['POST'])
@login_required
@permission_required('testcase_execute')
def bulk_execute_testcases():
    ids = request.form.getlist('testcase_ids')
    if not ids:
        flash('No test cases selected for execution.', 'warning')
        return redirect(url_for('testcases.list_testcases'))
    for tc_id in ids:
        testcase = TestCase.query.options(joinedload(TestCase.workflow)).get(tc_id)
        if testcase:
            # Simulate test execution
            status = random.choice(['passed', 'failed'])
            output = f"Simulated run for test case {testcase.name} (workflow: {testcase.workflow.name})"
            run = TestRun(
                test_case_id=testcase.id,
                executed_at=datetime.utcnow(),
                status=status,
                output=output,
                duration=round(random.uniform(0.1, 2.0), 2)
            )
            db.session.add(run)
            db.session.add(AuditLog(
                user=current_user.username,
                action='execute',
                filetype='testcase',
                details=f"Executed test case: {testcase.name} (ID: {testcase.id}), status: {status}"
            ))
    db.session.commit()
    flash(f'Executed {len(ids)} test case(s).', 'success')
    return redirect(url_for('testcases.list_testcases'))

@testcases.route('/testruns/<int:id>', methods=['GET'])
@login_required
def testrun_detail(id):
    testrun = TestRun.query.get_or_404(id)
    testcase = TestCase.query.get(testrun.test_case_id)
    workflow = Workflow.query.get(testcase.workflow_id) if testcase else None
    return render_template('testrun_detail.html', testrun=testrun, testcase=testcase, workflow=workflow)

@testcases.route('/testruns', methods=['GET'])
@login_required
def list_testruns():
    query = TestRun.query
    status = request.args.get('status')
    date = request.args.get('date')
    test_case_id = request.args.get('test_case_id', type=int)
    if status:
        query = query.filter_by(status=status)
    if date:
        try:
            dt = datetime.strptime(date, '%Y-%m-%d')
            next_day = dt + timedelta(days=1)
            query = query.filter(TestRun.executed_at >= dt, TestRun.executed_at < next_day)
        except Exception:
            pass
    if test_case_id:
        query = query.filter_by(test_case_id=test_case_id)
    runs = query.order_by(TestRun.executed_at.desc()).limit(100).all()
    return render_template('testruns_list.html', runs=runs, status=status, date=date, test_case_id=test_case_id)

@testcases.route('/testruns/export', methods=['GET'])
@login_required
def export_testruns():
    query = TestRun.query
    status = request.args.get('status')
    date = request.args.get('date')
    test_case_id = request.args.get('test_case_id', type=int)
    if status:
        query = query.filter_by(status=status)
    if date:
        try:
            dt = datetime.strptime(date, '%Y-%m-%d')
            next_day = dt + timedelta(days=1)
            query = query.filter(TestRun.executed_at >= dt, TestRun.executed_at < next_day)
        except Exception:
            pass
    if test_case_id:
        query = query.filter_by(test_case_id=test_case_id)
    runs = query.order_by(TestRun.executed_at.desc()).all()
    def generate():
        data = csv.writer([])
        header = ['Test Case', 'Workflow', 'Status', 'Executed At', 'Duration', 'Output']
        yield ','.join(header) + '\n'
        for run in runs:
            row = [
                run.test_case.name if run.test_case else '',
                run.test_case.workflow.name if run.test_case and run.test_case.workflow else '',
                run.status,
                run.executed_at.strftime('%Y-%m-%d %H:%M:%S'),
                str(run.duration),
                '"' + (run.output.replace('"', '""') if run.output else '') + '"'
            ]
            yield ','.join(row) + '\n'
    return Response(generate(), mimetype='text/csv', headers={
        'Content-Disposition': 'attachment; filename=testruns.csv'
    })

@testcases.route('/testcases/auditlog', methods=['GET'])
@login_required
def testcases_auditlog():
    query = AuditLog.query.filter_by(filetype='testcase')
    user = request.args.get('user')
    action = request.args.get('action')
    date = request.args.get('date')
    if user:
        query = query.filter_by(user=user)
    if action:
        query = query.filter_by(action=action)
    if date:
        try:
            dt = datetime.strptime(date, '%Y-%m-%d')
            next_day = dt + timedelta(days=1)
            query = query.filter(AuditLog.timestamp >= dt, AuditLog.timestamp < next_day)
        except Exception:
            pass
    logs = query.order_by(AuditLog.timestamp.desc()).limit(100).all()
    return render_template('testcases_auditlog.html', logs=logs, user=user, action=action, date=date)

@testcases.route('/testcases/<int:id>', methods=['GET'])
@login_required
def testcase_detail(id):
    testcase = TestCase.query.get_or_404(id)
    runs = TestRun.query.filter_by(test_case_id=id).order_by(TestRun.executed_at.desc()).all()
    workflow = Workflow.query.get(testcase.workflow_id)
    return render_template('testcases_detail.html', testcase=testcase, runs=runs, workflow=workflow)

@testcases.route('/testcases/<int:id>/clone', methods=['POST'])
@login_required
@permission_required('testcase_create')
def clone_testcase(id):
    orig = TestCase.query.get_or_404(id)
    new_tc = TestCase(
        name=orig.name + ' (Clone)',
        description=orig.description,
        schedule=orig.schedule,
        next_run_at=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.session.add(new_tc)
    db.session.commit()
    db.session.add(AuditLog(
        user=current_user.username,
        action='clone',
        filetype='testcase',
        details=f"Cloned test case: {orig.name} (ID: {orig.id}) to {new_tc.name} (ID: {new_tc.id})"
    ))
    db.session.commit()
    flash('Test case cloned successfully!', 'success')
    return redirect(url_for('testcases.edit_testcase', id=new_tc.id)) 