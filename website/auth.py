from flask import Blueprint, flash, render_template, request, url_for, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from .models import User
from .forms import LoginForm, RegisterForm
from . import db

# Create a blueprint - make sure all BPs have unique names
auth_bp = Blueprint('auth', __name__)

# this is a hint for a login function
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Handle both login and registration form submissions.
    login_form = LoginForm(prefix='login')
    register_form = RegisterForm(prefix='register')
    active_tab = request.args.get('tab', 'login')
    if active_tab not in {'login', 'register'}:
        active_tab = 'login'

    if request.method == 'POST':
        if register_form.submit.data:
            active_tab = 'register'
            if register_form.validate():
                email = register_form.email.data
                existing_user = db.session.scalar(
                    db.select(User).where(User.email == email)
                )
                if existing_user:
                    flash('An account with that email already exists.', 'danger')
                else:
                    password_hash = generate_password_hash(register_form.password.data)
                    new_user = User(
                        first_name=register_form.first_name.data,
                        last_name=register_form.last_name.data,
                        email=email,
                        password_hash=password_hash,
                        contact_number=register_form.contact_number.data,
                        street_address=register_form.street_address.data,
                    )
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
                email = login_form.email.data
                password = login_form.password.data
                user = db.session.scalar(db.select(User).where(User.email == email))
                if user is None:
                    flash('No account found with that email address.', 'danger')
                elif not check_password_hash(user.password_hash, password):
                    flash('Incorrect password', 'danger')
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
    # Log the current user out and redirect to home.
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))
