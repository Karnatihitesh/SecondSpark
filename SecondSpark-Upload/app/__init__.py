import os
from flask import Flask, render_template, g
from config import config
from app.models.user import db, User
from app.models.category import Category
from app.models.notification import Notification
from app.models.message import Message
from app.services.auth_service import get_current_user
from app.services.email_service import mail


def create_app(config_name='default'):
    """Flask application factory."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Ensure upload directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'projects'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'avatars'), exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)

    # Context processors to make user and global stats accessible in all templates
    @app.context_processor
    def inject_globals():
        user = get_current_user()
        categories = Category.query.order_by(Category.name.asc()).all()

        unread_notifs = 0
        unread_msgs = 0
        if user:
            unread_notifs = Notification.query.filter_by(user_id=user.id, is_read=False).count()
            unread_msgs = Message.query.filter_by(receiver_id=user.id, is_read=False).count()

        return {
            'current_user': user,
            'global_categories': categories,
            'unread_notifs_count': unread_notifs,
            'unread_msgs_count': unread_msgs,
            'app_name': 'SecondSpark',
            'app_tagline': 'Give Unfinished Ideas a Second Spark.'
        }

    # ── Template Filters ──────────────────────────────────────────────────────

    @app.template_filter('currency')
    def format_currency(value):
        """Format value as Indian Rupees (INR)."""
        if value is None or value == 0:
            return "Flexible / Open"
        try:
            v = float(value)
            if v >= 10_000_000:
                return f"\u20b9{v/10_000_000:.2f} Cr"
            elif v >= 100_000:
                return f"\u20b9{v/100_000:.2f} L"
            else:
                return f"\u20b9{v:,.0f}"
        except (ValueError, TypeError):
            return str(value)

    @app.template_filter('inr')
    def format_inr(value):
        """Always format as plain INR amount."""
        try:
            return f"\u20b9{float(value):,.2f}"
        except (ValueError, TypeError):
            return f"\u20b9{value}"

    @app.template_filter('timeago')
    def timeago_filter(dt):
        if not dt:
            return ''
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        diff = now - dt
        seconds = diff.total_seconds()
        if seconds < 60:
            return 'just now'
        elif seconds < 3600:
            minutes = int(seconds // 60)
            return f"{minutes}m ago"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            return f"{hours}h ago"
        elif seconds < 604800:
            days = int(seconds // 86400)
            return f"{days}d ago"
        else:
            return dt.strftime('%b %d, %Y')

    # ── Register Blueprints ───────────────────────────────────────────────────
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.projects import projects_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.messages import messages_bp
    from app.routes.notifications import notifications_bp
    from app.routes.reviews import reviews_bp
    from app.routes.reports import reports_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp
    from app.routes.payments import payments_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(payments_bp)

    # ── Error Handlers ────────────────────────────────────────────────────────
    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # Auto create tables within app context
    with app.app_context():
        db.create_all()

    return app
