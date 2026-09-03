import re
from functools import wraps
from flask import session, redirect, url_for, flash, request, abort, g, jsonify
from app.models.user import db, User


def get_current_user():
    """Retrieve currently authenticated user from session or cache on g."""
    user_id = session.get('user_id')
    if not user_id:
        g.current_user = None
        return None

    if hasattr(g, 'current_user') and g.current_user is not None and getattr(g.current_user, 'id', None) == user_id:
        return g.current_user
    
    user = db.session.get(User, user_id)
    if user and user.is_active:
        g.current_user = user
        return user
    else:
        session.pop('user_id', None)
        g.current_user = None
        return None


def login_required(f):
    """Decorator to require authenticated user session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.path.startswith('/api/'):
                next_url = request.referrer or request.url
                return jsonify({
                    'success': False,
                    'error': 'Authentication required',
                    'redirect': url_for('auth.login', next=next_url)
                }), 401
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            flash('Admin authentication required.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        if not user.is_admin:
            flash('Access denied: Administrator privileges required.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def validate_password_strength(password):
    """
    Ensure password has at least 8 characters, at least 1 digit, and 1 letter.
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Za-z]", password):
        return False, "Password must contain at least one letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."
    return True, ""


def slugify(text):
    """Generate a clean URL slug from text."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = re.sub(r'^-+|-+$', '', text)
    return text
