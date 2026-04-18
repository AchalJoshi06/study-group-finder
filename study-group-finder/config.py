import os


BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _get_database_url():
    database_url = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'app.db')}"
    )

    # Some providers expose postgres:// which SQLAlchemy no longer accepts.
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql://", 1)

    return database_url


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    SQLALCHEMY_DATABASE_URI = _get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_PRICE_MONTHLY_ID = os.getenv("STRIPE_PRICE_MONTHLY_ID", "")
    STRIPE_PRICE_YEARLY_ID = os.getenv("STRIPE_PRICE_YEARLY_ID", "")
    PREMIUM_MONTHLY_PRICE = os.getenv("PREMIUM_MONTHLY_PRICE", "$9.99")
    PREMIUM_YEARLY_PRICE = os.getenv("PREMIUM_YEARLY_PRICE", "$89.99")


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class ProductionConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "dev": DevelopmentConfig,
    "production": ProductionConfig,
    "prod": ProductionConfig,
}

