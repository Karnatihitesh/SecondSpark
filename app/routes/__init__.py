from app.routes.auth import auth_bp
from app.routes.main import main_bp
from app.routes.projects import projects_bp
from app.routes.dashboard import dashboard_bp
from app.routes.messages import messages_bp
from app.routes.notifications import notifications_bp
from app.routes.reviews import reviews_bp
from app.routes.reports import reports_bp
from app.routes.admin import admin_bp
from app.routes.api import api_bp

__all__ = [
    'auth_bp',
    'main_bp',
    'projects_bp',
    'dashboard_bp',
    'messages_bp',
    'notifications_bp',
    'reviews_bp',
    'reports_bp',
    'admin_bp',
    'api_bp'
]
