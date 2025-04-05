from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from app.models import User, db, get_user_by_email, get_user_by_username

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = get_user_by_email(email)
        
        # Check if user exists and password is correct
        if not user or not user.check_password(password):
            flash('Please check your login details and try again.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Log in the user
        login_user(user, remember=remember)
        
        # Redirect to the page they were trying to access
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('main.index'))
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check if user already exists
        if get_user_by_email(email):
            flash('Email address already exists.', 'danger')
            return redirect(url_for('auth.register'))
        
        if get_user_by_username(username):
            flash('Username already exists.', 'danger')
            return redirect(url_for('auth.register'))
        
        # Create a new user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page and editing."""
    if request.method == 'POST':
        # Update profile information
        profile_data = {
            'personality': request.form.get('personality'),
            'writing_style': request.form.get('writing_style'),
            'expertise': request.form.get('expertise'),
            'background': request.form.get('background'),
            'twitter': request.form.get('twitter'),
            'linkedin': request.form.get('linkedin'),
            'instagram': request.form.get('instagram'),
            'website': request.form.get('website')
        }
        
        current_user.update_profile(profile_data)
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('profile.html') 