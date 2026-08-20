import os
import json
import secrets
import urllib.parse
import urllib.request
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g, current_app
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

        # Form validation
        if not login_input or not password:
            flash('Please enter both your email/username and password.', 'danger')
            return render_template('login.html')

        # Case-insensitive lookup by email or username
        user = User.query.filter(
            (db.func.lower(User.email) == login_input) | (db.func.lower(User.username) == login_input)
        ).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been suspended. Please contact support.', 'danger')
                return render_template('login.html')

            # Establish secure session
            session['user_id'] = user.id
            if remember:
                session.permanent = True
            g.current_user = user

            flash(f'Welcome back, {user.full_name}!', 'success')
            next_url = request.args.get('next')
            if next_url and next_url.startswith('/') and not next_url.startswith('//'):
                return redirect(next_url)
            
            # Dynamic role-based redirection from database
            if user.is_admin:
                return redirect(url_for('admin.index'))
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid email/username or password. Please check your credentials and try again.', 'danger')
            return render_template('login.html')

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('oauth_state', None)
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


# ── Real Google OAuth 2.0 & Identity Services Integration ─────────────────────
@auth_bp.route('/google')
def google_login():
    """Initiate standard Google OAuth 2.0 authorization redirect."""
    if get_current_user():
        return redirect(url_for('dashboard.index'))

    import urllib.parse
    from flask import current_app

    client_id = current_app.config.get('GOOGLE_CLIENT_ID') or os.environ.get('GOOGLE_CLIENT_ID')
    
    # Store return URL
    next_url = request.args.get('next', '')
    if next_url:
        session['next_url'] = next_url

    # Check if Google OAuth Client ID is configured
    if not client_id:
        flash(
            'Google OAuth is not configured yet. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET '
            'in your environment settings to enable live Google authentication.',
            'warning'
        )
        return redirect(url_for('auth.login'))

    # Generate secure state token for CSRF protection
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state

    # Build standard Google OAuth 2.0 authorization URL
    redirect_uri = current_app.config.get('GOOGLE_REDIRECT_URI') or url_for('auth.google_callback', _external=True)
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'prompt': 'select_account',
        'access_type': 'offline'
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)


@auth_bp.route('/google/callback', methods=['GET', 'POST'])
def google_callback():
    """Handle Google OAuth 2.0 authorization code exchange and token verification."""
    if get_current_user():
        return redirect(url_for('dashboard.index'))

    import json, urllib.request, urllib.parse
    from flask import current_app

    client_id = current_app.config.get('GOOGLE_CLIENT_ID') or os.environ.get('GOOGLE_CLIENT_ID')
    client_secret = current_app.config.get('GOOGLE_CLIENT_SECRET') or os.environ.get('GOOGLE_CLIENT_SECRET')

    verified_email = None
    verified_name = None
    verified_picture = None

    # Handle POST from Google Identity Services (GSI) One-Tap / Button (ID Token)
    if request.method == 'POST':
        credential = request.form.get('credential')
        if credential:
            try:
                # Verify token with Google's public tokeninfo endpoint
                verify_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}"
                req = urllib.request.Request(verify_url, headers={'User-Agent': 'SecondSpark-Auth'})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    token_info = json.loads(resp.read().decode('utf-8'))
                    verified_email = token_info.get('email')
                    verified_name = token_info.get('name')
                    verified_picture = token_info.get('picture')
            except Exception as e:
                flash('Google authentication verification failed. Please try again.', 'danger')
                return redirect(url_for('auth.login'))

    # Handle GET from Google OAuth 2.0 Authorization Code flow
    elif request.method == 'GET':
        error = request.args.get('error')
        if error:
            flash(f'Google authentication was cancelled or encountered an error ({error}).', 'warning')
            return redirect(url_for('auth.login'))

        code = request.args.get('code')
        state = request.args.get('state')

        # Verify CSRF state
        saved_state = session.pop('oauth_state', None)
        if not state or state != saved_state:
            flash('Security validation failed (state mismatch). Please try again.', 'danger')
            return redirect(url_for('auth.login'))

        if code:
            redirect_uri = current_app.config.get('GOOGLE_REDIRECT_URI') or url_for('auth.google_callback', _external=True)
            token_url = "https://oauth2.googleapis.com/token"
            token_data = urllib.parse.urlencode({
                'code': code,
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            }).encode('utf-8')

            try:
                # Exchange code for access token and ID token
                token_req = urllib.request.Request(
                    token_url,
                    data=token_data,
                    headers={'Content-Type': 'application/x-www-form-urlencoded', 'User-Agent': 'SecondSpark-Auth'}
                )
                with urllib.request.urlopen(token_req, timeout=12) as token_resp:
                    token_res_data = json.loads(token_resp.read().decode('utf-8'))
                    access_token = token_res_data.get('access_token')

                # Fetch verified user profile from Google UserInfo endpoint
                userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
                userinfo_req = urllib.request.Request(
                    userinfo_url,
                    headers={'Authorization': f'Bearer {access_token}', 'User-Agent': 'SecondSpark-Auth'}
                )
                with urllib.request.urlopen(userinfo_req, timeout=10) as userinfo_resp:
                    user_info = json.loads(userinfo_resp.read().decode('utf-8'))
                    verified_email = user_info.get('email')
                    verified_name = user_info.get('name')
                    verified_picture = user_info.get('picture')

            except Exception as e:
                flash('Failed to complete Google authentication. Please try logging in with email and password.', 'danger')
                return redirect(url_for('auth.login'))

    if not verified_email:
        flash('Could not retrieve email from Google authentication. Please try again.', 'danger')
        return redirect(url_for('auth.login'))

    verified_email = verified_email.strip().lower()

    # Retrieve or create user record in database
    user = User.query.filter(db.func.lower(User.email) == verified_email).first()

    if not user:
        # Generate base username from email prefix
        base_username = verified_email.split('@')[0].replace('.', '_')
        username = base_username
        suffix = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}_{suffix}"
            suffix += 1

        full_name = verified_name or verified_email.split('@')[0].replace('.', ' ').title()
        user = User(
            username=username,
            email=verified_email,
            full_name=full_name,
            avatar_url=verified_picture or '/static/images/default-avatar.svg',
            role='user'  # Standard user role dynamically assigned from database
        )
        user.set_password(secrets.token_urlsafe(32))
        try:
            db.session.add(user)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('Error creating account via Google. Please try again.', 'danger')
            return redirect(url_for('auth.login'))
    else:
        # Update avatar if user has default avatar and Google provided one
        if verified_picture and (not user.avatar_url or 'default-avatar' in user.avatar_url):
            user.avatar_url = verified_picture
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()

    # Establish authenticated user session
    session['user_id'] = user.id
    session.permanent = True
    g.current_user = user

    flash(f'👋 Welcome, {user.full_name}! Successfully authenticated with Google.', 'success')

    next_url = session.pop('next_url', None)
    if next_url and next_url.startswith('/') and not next_url.startswith('//'):
        return redirect(next_url)

    # Dynamic role-based redirect
    if user.is_admin:
        return redirect(url_for('admin.index'))
    return redirect(url_for('dashboard.index'))



