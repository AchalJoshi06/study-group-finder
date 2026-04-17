from routes.auth_routes import auth_bp
from routes.chat_routes import chat_bp
from routes.group_routes import group_bp
from routes.subscription_routes import subscription_bp
from routes.user_routes import user_bp

__all__ = ["auth_bp", "chat_bp", "group_bp", "subscription_bp", "user_bp"]
