from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from .models import Label, TestCase, TestCaseLabel
from . import db
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional
from functools import wraps

labels = Blueprint('labels', __name__)

def permission_required(permission_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if getattr(current_user, 'role', None) and (current_user.role.name == 'admin' or any(p.name == permission_name for p in current_user.role.permissions)):
                return f(*args, **kwargs)
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('dashboard'))
        return decorated_function
    return decorator

class LabelForm(FlaskForm):
    name = StringField('Label Name', validators=[DataRequired()])
    color = StringField('Color (Hex)', default='#007bff')
    description = TextAreaField('Description', validators=[Optional()])

@labels.route('/labels')
@login_required
def list_labels():
    labels = Label.query.order_by(Label.name).all()
    return render_template('labels.html', labels=labels)

@labels.route('/labels/new', methods=['GET', 'POST'])
@login_required
@permission_required('label_manage')
def create_label():
    form = LabelForm()
    if form.validate_on_submit():
        label = Label(
            name=form.name.data,
            color=form.color.data,
            description=form.description.data
        )
        db.session.add(label)
        db.session.commit()
        flash('Label created successfully!', 'success')
        return redirect(url_for('labels.list_labels'))
    
    return render_template('label_form.html', form=form, action='Create')

@labels.route('/labels/<int:label_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('label_manage')
def edit_label(label_id):
    label = Label.query.get_or_404(label_id)
    form = LabelForm(obj=label)
    
    if form.validate_on_submit():
        label.name = form.name.data
        label.color = form.color.data
        label.description = form.description.data
        db.session.commit()
        flash('Label updated successfully!', 'success')
        return redirect(url_for('labels.list_labels'))
    
    return render_template('label_form.html', form=form, action='Edit')

@labels.route('/labels/<int:label_id>/delete', methods=['POST'])
@login_required
@permission_required('label_manage')
def delete_label(label_id):
    label = Label.query.get_or_404(label_id)
    db.session.delete(label)
    db.session.commit()
    flash('Label deleted successfully!', 'success')
    return redirect(url_for('labels.list_labels'))

@labels.route('/labels/<int:label_id>/testcases')
@login_required
def label_testcases(label_id):
    label = Label.query.get_or_404(label_id)
    test_cases = TestCase.query.join(TestCaseLabel).filter(TestCaseLabel.label_id == label_id).all()
    return render_template('label_testcases.html', label=label, test_cases=test_cases)

@labels.route('/api/labels')
@login_required
def api_labels():
    """API endpoint to get all labels for dropdowns"""
    labels = Label.query.order_by(Label.name).all()
    return jsonify([{
        'id': label.id,
        'name': label.name,
        'color': label.color
    } for label in labels])

@labels.route('/api/testcases/<int:testcase_id>/labels', methods=['GET', 'POST', 'DELETE'])
@login_required
def api_testcase_labels(testcase_id):
    """API endpoint to manage test case labels"""
    test_case = TestCase.query.get_or_404(testcase_id)
    
    if request.method == 'GET':
        labels = [{
            'id': label.id,
            'name': label.name,
            'color': label.color
        } for label in test_case.labels]
        return jsonify(labels)
    
    elif request.method == 'POST':
        data = request.get_json()
        label_id = data.get('label_id')
        
        if not label_id:
            return jsonify({'error': 'Label ID required'}), 400
        
        # Check if label already exists
        existing = TestCaseLabel.query.filter_by(
            test_case_id=testcase_id, 
            label_id=label_id
        ).first()
        
        if existing:
            return jsonify({'error': 'Label already assigned'}), 400
        
        test_case_label = TestCaseLabel(
            test_case_id=testcase_id,
            label_id=label_id
        )
        db.session.add(test_case_label)
        db.session.commit()
        
        return jsonify({'message': 'Label assigned successfully'})
    
    elif request.method == 'DELETE':
        data = request.get_json()
        label_id = data.get('label_id')
        
        if not label_id:
            return jsonify({'error': 'Label ID required'}), 400
        
        test_case_label = TestCaseLabel.query.filter_by(
            test_case_id=testcase_id,
            label_id=label_id
        ).first()
        
        if test_case_label:
            db.session.delete(test_case_label)
            db.session.commit()
            return jsonify({'message': 'Label removed successfully'})
        else:
            return jsonify({'error': 'Label not found'}), 404 