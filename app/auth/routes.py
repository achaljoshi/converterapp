from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from . import auth
from ..models import User, Role, Permission
from .. import db, login_manager
from .forms import LoginForm, RegistrationForm, RoleForm, PermissionForm, RolePermissionForm, UserRoleForm, UserCreateForm, UserEditForm
from functools import wraps
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    return render_template('login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists')
            return render_template('register.html', form=form)
        user = User(username=form.username.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please log in.')
        return redirect(url_for('auth.login'))
    return render_template('register.html', form=form)

def admin_or_permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if getattr(current_user, 'role', None) and (current_user.role.name == 'admin' or any(p.name == permission for p in current_user.role.permissions)):
                return f(*args, **kwargs)
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('dashboard'))
        return decorated_function
    return decorator

@auth.route('/roles')
@login_required
@admin_or_permission_required('role_manage')
def list_roles():
    roles = Role.query.all()
    return render_template('roles.html', roles=roles)

@auth.route('/roles/add', methods=['GET', 'POST'])
@login_required
@admin_or_permission_required('role_manage')
def add_role():
    form = RoleForm()
    if form.validate_on_submit():
        role = Role(name=form.name.data, description=form.description.data)
        db.session.add(role)
        db.session.commit()
        flash('Role added successfully!', 'success')
        return redirect(url_for('auth.list_roles'))
    return render_template('role_form.html', form=form, action='Add')

@auth.route('/roles/<int:role_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_or_permission_required('role_manage')
def edit_role(role_id):
    role = Role.query.get_or_404(role_id)
    form = RoleForm(obj=role)
    if form.validate_on_submit():
        role.name = form.name.data
        role.description = form.description.data
        db.session.commit()
        flash('Role updated successfully!', 'success')
        return redirect(url_for('auth.list_roles'))
    return render_template('role_form.html', form=form, action='Edit')

@auth.route('/roles/<int:role_id>/delete', methods=['POST'])
@login_required
@admin_or_permission_required('role_manage')
def delete_role(role_id):
    role = Role.query.get_or_404(role_id)
    db.session.delete(role)
    db.session.commit()
    flash('Role deleted successfully!', 'success')
    return redirect(url_for('auth.list_roles'))

@auth.route('/permissions')
@login_required
@admin_or_permission_required('permission_manage')
def list_permissions():
    permissions = Permission.query.all()
    return render_template('permissions.html', permissions=permissions)

@auth.route('/permissions/add', methods=['GET', 'POST'])
@login_required
@admin_or_permission_required('permission_manage')
def add_permission():
    form = PermissionForm()
    if form.validate_on_submit():
        perm = Permission(name=form.name.data, description=form.description.data)
        db.session.add(perm)
        db.session.commit()
        flash('Permission added successfully!', 'success')
        return redirect(url_for('auth.list_permissions'))
    return render_template('permission_form.html', form=form, action='Add')

@auth.route('/permissions/<int:perm_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_or_permission_required('permission_manage')
def edit_permission(perm_id):
    perm = Permission.query.get_or_404(perm_id)
    form = PermissionForm(obj=perm)
    if form.validate_on_submit():
        perm.name = form.name.data
        perm.description = form.description.data
        db.session.commit()
        flash('Permission updated successfully!', 'success')
        return redirect(url_for('auth.list_permissions'))
    return render_template('permission_form.html', form=form, action='Edit')

@auth.route('/permissions/<int:perm_id>/delete', methods=['POST'])
@login_required
@admin_or_permission_required('permission_manage')
def delete_permission(perm_id):
    perm = Permission.query.get_or_404(perm_id)
    db.session.delete(perm)
    db.session.commit()
    flash('Permission deleted successfully!', 'success')
    return redirect(url_for('auth.list_permissions'))

@auth.route('/roles/<int:role_id>/permissions', methods=['GET', 'POST'])
@login_required
@admin_or_permission_required('role_manage')
def assign_permissions(role_id):
    role = Role.query.get_or_404(role_id)
    form = RolePermissionForm()
    # Populate choices with all permissions
    form.permissions.choices = [(p.id, p.name) for p in Permission.query.order_by(Permission.name).all()]
    if request.method == 'POST' and 'add' in request.form:
        perm_id = form.permissions.data
        perm = Permission.query.get(perm_id)
        if perm and perm not in role.permissions:
            role.permissions.append(perm)
            db.session.commit()
            flash('Permission assigned to role.', 'success')
        return redirect(url_for('auth.assign_permissions', role_id=role.id))
    if request.method == 'POST' and 'remove' in request.form:
        perm_id = int(request.form.get('remove'))
        perm = Permission.query.get(perm_id)
        if perm and perm in role.permissions:
            role.permissions.remove(perm)
            db.session.commit()
            flash('Permission removed from role.', 'success')
        return redirect(url_for('auth.assign_permissions', role_id=role.id))
    return render_template('role_permissions.html', role=role, form=form)

@auth.route('/users')
@login_required
@admin_or_permission_required('role_manage')
def list_users():
    users = User.query.all()
    return render_template('users.html', users=users)

@auth.route('/users/assign-role', methods=['GET', 'POST'])
@login_required
@admin_or_permission_required('role_manage')
def assign_role():
    form = UserRoleForm()
    # Populate choices
    form.user.choices = [(u.id, u.username) for u in User.query.order_by(User.username).all()]
    form.role.choices = [(r.id, r.name) for r in Role.query.order_by(Role.name).all()]
    if form.validate_on_submit():
        user = User.query.get(form.user.data)
        role = Role.query.get(form.role.data)
        if user and role:
            user.role = role
            db.session.commit()
            flash(f"Role '{role.name}' assigned to user '{user.username}'.", 'success')
            return redirect(url_for('auth.list_users'))
    return render_template('user_role_form.html', form=form)

@auth.route('/users/add', methods=['GET', 'POST'])
@login_required
@admin_or_permission_required('role_manage')
def add_user():
    form = UserCreateForm()
    form.role.choices = [(r.id, r.name) for r in Role.query.order_by(Role.name).all()]
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists.', 'danger')
            return render_template('user_form.html', form=form, action='Add')
        if form.email.data and User.query.filter_by(email=form.email.data).first():
            flash('Email already exists.', 'danger')
            return render_template('user_form.html', form=form, action='Add')
        user = User(
            username=form.username.data,
            email=form.email.data,
            role_id=form.role.data,
            date_joined=datetime.utcnow()
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('User created successfully!', 'success')
        return redirect(url_for('auth.list_users'))
    return render_template('user_form.html', form=form, action='Add')

@auth.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_or_permission_required('role_manage')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserEditForm(obj=user)
    form.role.choices = [(r.id, r.name) for r in Role.query.order_by(Role.name).all()]
    if form.validate_on_submit():
        if User.query.filter(User.username == form.username.data, User.id != user.id).first():
            flash('Username already exists.', 'danger')
            return render_template('user_form.html', form=form, action='Edit')
        if form.email.data and User.query.filter(User.email == form.email.data, User.id != user.id).first():
            flash('Email already exists.', 'danger')
            return render_template('user_form.html', form=form, action='Edit')
        user.username = form.username.data
        user.email = form.email.data
        user.role_id = form.role.data
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('auth.list_users'))
    # Set current role in form
    if request.method == 'GET':
        form.role.data = user.role_id
    return render_template('user_form.html', form=form, action='Edit') 