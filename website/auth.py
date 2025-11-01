from flask import Blueprint, flash, render_template, request, url_for, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from sqlalchemy import or_
from .models import User
from .forms import LoginForm, RegisterForm
from . import db

# Create a blueprint - make sure all BPs have unique names
auth_bp = Blueprint('auth', __name__)

# this is a hint for a login function
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(prefix='login')
    register_form = RegisterForm(prefix='register')
    active_tab = request.args.get('tab', 'login')
    if active_tab not in {'login', 'register'}:
        active_tab = 'login'

    if request.method == 'POST':
        if register_form.submit.data:
            active_tab = 'register'
            if register_form.validate():
                user_name = register_form.user_name.data
                email = register_form.email.data
                existing_user = db.session.scalar(
                    db.select(User).where(or_(User.name == user_name, User.email == email))
                )
                if existing_user:
                    flash('An account with that username or email already exists.', 'danger')
                else:
                    password_hash = generate_password_hash(register_form.password.data)
                    new_user = User(name=user_name, email=email, password_hash=password_hash)
                    db.session.add(new_user)
                    db.session.commit()
                    login_user(new_user)
                    flash('Welcome to LocalConcerts! Your account is ready.', 'success')
                    next_url = request.args.get('next')
                    if not next_url or not next_url.startswith('/'):
                        next_url = url_for('main.index')
                    return redirect(next_url)
            else:
                flash('Please fix the highlighted errors and try again.', 'danger')

        elif login_form.submit.data:
            active_tab = 'login'
            if login_form.validate():
                user_name = login_form.user_name.data
                password = login_form.password.data
                user = db.session.scalar(db.select(User).where(User.name == user_name))
                if user is None:
                    flash('Incorrect user name', 'danger')
                elif not check_password_hash(user.password_hash, password):
                    flash('Incorrect password', 'danger')  # takes the hash and cleartext password
                else:
                    login_user(user)
                    next_url = request.args.get('next')
                    if not next_url or not next_url.startswith('/'):
                        next_url = url_for('main.index')
                    return redirect(next_url)
            else:
                flash('Please fix the highlighted errors and try again.', 'danger')

    return render_template(
        'user.html',
        login_form=login_form,
        register_form=register_form,
        heading='Account',
        active_tab=active_tab,
        user=current_user if current_user.is_authenticated else None,
    )


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))
