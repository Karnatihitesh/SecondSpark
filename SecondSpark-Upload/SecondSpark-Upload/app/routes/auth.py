import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from app.models.user import db, User, VerificationCode
from app.services.auth_service import get_current_user, login_required, validate_password_strength
from app.services.project_service import save_uploaded_file
from app.services.email_service import send_otp_email

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


# ── Forgot Password Step 1: Request OTP ───────────────────────────────────────
@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if get_current_user():
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if not email:
            flash('Please enter your email address.', 'danger')
            return render_template('forgot_password.html')

        user = User.query.filter_by(email=email).first()
        if not user:
            # Security: don't reveal whether the email exists
            flash('If that email is registered, a 6-digit verification code has been sent to it.', 'info')
            return redirect(url_for('auth.verify_otp'))

        # Generate OTP (10-minute expiry)
        otp = VerificationCode.generate(email=email, purpose='password_reset', ttl_minutes=10)

        # Send real email via Gmail SMTP
        sent = send_otp_email(to=email, otp_code=otp.code, name=user.full_name)

        if sent:
            flash(
                f'✅ A 6-digit verification code has been sent to <strong>{email}</strong>. '
                f'Check your inbox (and spam folder).',
                'success'
            )
        else:
            # Email failed — show code directly so flow isn't broken (dev fallback)
            flash(
                f'⚠️ Email delivery failed. Your code is: '
                f'<strong style="font-size:1.4rem;letter-spacing:0.12em;">{otp.code}</strong> '
                f'(valid 10 min). Please configure MAIL_PASSWORD in .env for real delivery.',
                'warning'
            )

        session['reset_email'] = email
        return redirect(url_for('auth.verify_otp'))

    return render_template('forgot_password.html')



# ── Forgot Password Step 2: Verify OTP ────────────────────────────────────────
@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if get_current_user():
        return redirect(url_for('dashboard.index'))

    email = session.get('reset_email') or request.form.get('email', '').strip().lower()
    if not email:
        flash('Session expired. Please restart the password reset.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        code = request.form.get('otp_code', '').strip()
        if not code or len(code) != 6 or not code.isdigit():
            flash('Please enter the complete 6-digit code.', 'danger')
            return render_template('verify_otp.html', email=email)

        otp = VerificationCode.verify(email=email, code=code, purpose='password_reset')
        if not otp:
            flash('Invalid or expired code. Please request a new one.', 'danger')
            return render_template('verify_otp.html', email=email)

        otp.mark_used()
        import secrets as _sec
        reset_token = _sec.token_urlsafe(32)
        session['reset_token'] = reset_token
        session['reset_email'] = email
        return redirect(url_for('auth.reset_password'))

    return render_template('verify_otp.html', email=email)


# ── Forgot Password Step 3: Set New Password ──────────────────────────────────
@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if get_current_user():
        return redirect(url_for('dashboard.index'))

    email = session.get('reset_email')
    token = session.get('reset_token')

    if not email or not token:
        flash('Invalid or expired reset link. Please start over.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        form_token = request.form.get('token', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if form_token != token:
            flash('Security token mismatch. Please start over.', 'danger')
            return redirect(url_for('auth.forgot_password'))

        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('reset_password.html', email=email, token=token)

        is_valid, msg = validate_password_strength(new_password)
        if not is_valid:
            flash(msg, 'danger')
            return render_template('reset_password.html', email=email, token=token)

        user = User.query.filter_by(email=email).first()
        if not user:
            flash('Account not found.', 'danger')
            return redirect(url_for('auth.forgot_password'))

        user.set_password(new_password)
        db.session.commit()

        session.pop('reset_email', None)
        session.pop('reset_token', None)
        flash('Password updated successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('reset_password.html', email=email, token=token)



@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if get_current_user():
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip().lower()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        skills = request.form.get('skills', '').strip()
        location = request.form.get('location', '').strip()

        # Validations
        if not full_name or not username or not email or not password:
            flash('All required fields must be filled.', 'danger')
            return render_template('register.html', form_data=request.form)

        if len(username) < 3:
            flash('Username must be at least 3 characters long.', 'danger')
            return render_template('register.html', form_data=request.form)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html', form_data=request.form)

        is_valid, msg = validate_password_strength(password)
        if not is_valid:
            flash(msg, 'danger')
            return render_template('register.html', form_data=request.form)

        # Check existing user
        if User.query.filter_by(username=username).first():
            flash('Username is already taken. Please choose another.', 'danger')
            return render_template('register.html', form_data=request.form)

        if User.query.filter_by(email=email).first():
            flash('An account with this email already exists.', 'danger')
            return render_template('register.html', form_data=request.form)

        # Create user
        try:
            user = User(
                full_name=full_name,
                username=username,
                email=email,
                skills=skills,
                location=location,
                role='user'
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            # Automatically log in
            session['user_id'] = user.id
            flash(f'Welcome to SecondSpark, {user.full_name}! Your account has been created.', 'success')
            return redirect(url_for('dashboard.index'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
            return render_template('register.html', form_data=request.form)

    return render_template('register.html', form_data={})


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if get_current_user():
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        login_input = request.form.get('login_input', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        if not login_input or not password:
            flash('Please provide both username/email and password.', 'danger')
            return render_template('login.html')

        # Check by email or username
        user = User.query.filter(
            (User.email == login_input) | (User.username == login_input)
        ).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been suspended. Please contact support.', 'danger')
                return render_template('login.html')

            session['user_id'] = user.id
            if remember:
                session.permanent = True
            
            flash(f'Welcome back, {user.full_name}!', 'success')
            next_url = request.args.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid username/email or password.', 'danger')
            return render_template('login.html')

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    g.current_user = None
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = get_current_user()

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        bio = request.form.get('bio', '').strip()
        skills = request.form.get('skills', '').strip()
        location = request.form.get('location', '').strip()
        
        # Avatar file upload
        avatar_file = request.files.get('avatar')
        if avatar_file and avatar_file.filename:
            avatar_url = save_uploaded_file(avatar_file, subfolder='avatars', is_image=True)
            if avatar_url:
                user.avatar_url = avatar_url

        # Password change
        new_password = request.form.get('new_password', '')
        if new_password:
            current_password = request.form.get('current_password', '')
            if not user.check_password(current_password):
                flash('Current password is incorrect.', 'danger')
                return render_template('profile.html', user=user)
            
            is_valid, msg = validate_password_strength(new_password)
            if not is_valid:
                flash(msg, 'danger')
                return render_template('profile.html', user=user)
            
            user.set_password(new_password)

        if full_name:
            user.full_name = full_name
        user.bio = bio
        user.skills = skills
        user.location = location

        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('auth.profile'))
        except Exception as e:
            db.session.rollback()
            flash('Error saving profile changes.', 'danger')

    return render_template('profile.html', user=user)


@auth_bp.route('/user/<username>')
def public_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    projects = user.projects.order_by(db.desc(db.text('created_at'))).all()
    reviews = user.reviews_received.order_by(db.desc(db.text('created_at'))).all()
    rating_summary = user.rating_summary
    return render_template('profile.html', user=user, is_public=True, projects=projects, reviews=reviews, rating_summary=rating_summary)
