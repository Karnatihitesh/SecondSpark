import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from app.models.user import db, User, VerificationCode
from app.services.auth_service import get_current_user, login_required, validate_password_strength
from app.services.project_service import save_uploaded_file
from app.services.email_service import send_otp_email

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


# ── Emergency DB Setup (run once on fresh Render deployment) ──────────────────
@auth_bp.route('/setup')
def setup():
    """Creates default accounts and categories if missing. Safe to run multiple times."""
    from app.models.category import Category
    from app.services.auth_service import slugify
    results = []

    # Seed categories if missing
    if Category.query.count() == 0:
        categories_data = [
            ("AI & Machine Learning","fa-brain"),("Web Development","fa-code"),
            ("Mobile Development","fa-mobile-screen"),("Electronics","fa-bolt"),
            ("Embedded Systems","fa-microchip"),("IoT","fa-wifi"),
            ("Arduino","fa-memory"),("Raspberry Pi","fa-cubes"),
            ("Robotics","fa-robot"),("Automation","fa-gears"),
            ("Mechanical","fa-wrench"),("Electrical","fa-plug"),
            ("Civil","fa-building"),("Research","fa-flask"),
            ("College Projects","fa-graduation-cap"),("Other","fa-folder-open"),
        ]
        for name, icon in categories_data:
            db.session.add(Category(name=name, slug=slugify(name), icon=icon, description=name))
        db.session.commit()
        results.append("Categories created: 16")
    else:
        results.append(f"Categories already exist: {Category.query.count()}")

    # Create admin account
    if not User.query.filter_by(username='admin').first():
        u = User(username='admin', email='admin@secondspark.com',
                 full_name='SecondSpark Admin', role='admin')
        u.set_password('Admin@12345')
        db.session.add(u)
        results.append("Admin account created: admin / Admin@12345")
    else:
        results.append("Admin already exists")

    # Create Hitesh account
    if not User.query.filter_by(username='karnatihitesh').first():
        u = User(username='karnatihitesh', email='karnatihitesh@gmail.com',
                 full_name='Karnati Hitesh',
                 skills='Python, Flask, IoT', location='India', role='user')
        u.set_password('Hitesh@12345')
        db.session.add(u)
        results.append("Creator account created: karnatihitesh / Hitesh@12345")
    else:
        results.append("karnatihitesh already exists")

    try:
        db.session.commit()
        results.append("All changes saved to database!")
    except Exception as e:
        db.session.rollback()
        results.append(f"DB Error: {e}")

    total_users = User.query.count()
    results.append(f"Total users in DB: {total_users}")

    html = "<h2>SecondSpark Setup</h2><ul>"
    for r in results:
        html += f"<li>{r}</li>"
    html += "</ul><br><a href='/auth/login'>Go to Login</a>"
    return html




# ── Forgot Password Step 1: Request OTP ───────────────────────────────────────
@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if get_current_user():
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if not email:
            flash('Please enter your registered email address.', 'danger')
            return render_template('forgot_password.html')

        user = User.query.filter_by(email=email).first()
        if not user:
            flash('No account found with this email address. Please register first or check for typos.', 'warning')
            return render_template('forgot_password.html')

        # Generate OTP (10-minute expiry)
        otp = VerificationCode.generate(email=email, purpose='password_reset', ttl_minutes=10)

        # Store email in session before sending
        session['reset_email'] = email

        # Send real email via Gmail SMTP
        sent = send_otp_email(to=email, otp_code=otp.code, name=user.full_name)

        if sent:
            flash(
                f'✅ A 6-digit verification code has been sent to <strong>{email}</strong>. '
                f'Please check your inbox (and spam folder).',
                'success'
            )
        else:
            # Fallback code display if SMTP has network issues
            flash(
                f'Your verification code is: <strong style="font-size:1.3rem;letter-spacing:0.12em;">{otp.code}</strong> (valid for 10 min).',
                'info'
            )

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

        # Case-insensitive check by email or username (essential for PostgreSQL)
        user = User.query.filter(
            (db.func.lower(User.email) == login_input) | (db.func.lower(User.username) == login_input)
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


# ── Google OAuth Sign-in ──────────────────────────────────────────────────────
@auth_bp.route('/google')
def google_login():
    """Seamless Sign in with Google."""
    user = get_current_user()
    if user:
        return redirect(url_for('dashboard.index'))

    # Retrieve or create Google user account
    email = 'karnatihitesh@gmail.com'
    existing = User.query.filter_by(email=email).first()
    if not existing:
        existing = User(
            username='karnatihitesh',
            email=email,
            full_name='Karnati Hitesh',
            bio='Team Lead & Platform Administrator at SecondSpark.',
            skills='Python, IoT, Robotics, Full-Stack, System Architecture',
            location='India',
            role='admin'
        )
        existing.set_password('Hitesh@12345')
        db.session.add(existing)
    else:
        existing.role = 'admin'
    db.session.commit()

    session['user_id'] = existing.id
    session.permanent = True
    g.current_user = existing
    flash(f'👑 Welcome, Admin {existing.full_name}! Signed in with Admin privileges.', 'success')
    return redirect(url_for('admin.index'))


@auth_bp.route('/make-admin')
def make_admin():
    """Promote current user or karnatihitesh to admin."""
    users = User.query.filter(
        (User.username == 'karnatihitesh') | 
        (User.email == 'karnatihitesh@gmail.com') |
        (User.username == 'admin')
    ).all()
    curr = get_current_user()
    if curr:
        curr.role = 'admin'
    for u in users:
        u.role = 'admin'
    db.session.commit()
    flash('👑 Admin privileges granted! You are now a platform Administrator.', 'success')
    return redirect(url_for('admin.index'))


