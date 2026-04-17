import os
from datetime import datetime, timedelta

from flask import Flask, render_template
from flask_login import current_user

from config import CONFIG_MAP, DevelopmentConfig
from extensions import db, init_extensions
from models.chat_message import ChatMessage
from models.group import StudyGroup
from models.session import GroupSession
from models.membership import GroupMember
from models.subscription import Subscription
from models.user import User
from routes.auth_routes import auth_bp
from routes.chat_routes import chat_bp
from routes.group_routes import group_bp
from routes.subscription_routes import subscription_bp
from routes.user_routes import user_bp
from services.subscription_service import get_plan_badge_label, get_usage_snapshot, is_premium


def create_app(config_name=None):
    app = Flask(__name__, instance_relative_config=True)

    resolved_config = (config_name or os.getenv("FLASK_CONFIG", "development")).lower()
    app.config.from_object(CONFIG_MAP.get(resolved_config, DevelopmentConfig))

    init_extensions(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(group_bp)
    app.register_blueprint(subscription_bp)
    app.register_blueprint(user_bp)

    @app.context_processor
    def inject_plan_context():
        if not current_user.is_authenticated:
            return {
                "current_plan_label": "",
                "current_user_is_premium": False,
                "current_usage_snapshot": None,
            }

        return {
            "current_plan_label": get_plan_badge_label(current_user),
            "current_user_is_premium": is_premium(current_user),
            "current_usage_snapshot": get_usage_snapshot(current_user),
        }

    @app.route("/")
    def index():
        recent_groups = (
            StudyGroup.query.filter_by(is_private=False)
            .order_by(StudyGroup.created_at.desc())
            .limit(6)
            .all()
        )
        return render_template("index.html", recent_groups=recent_groups)

    @app.cli.command("init-db")
    def init_db_command():
        db.create_all()
        print("Database initialized.")

    @app.cli.command("seed-db")
    def seed_db_command():
        db.create_all()

        if User.query.count() > 0:
            print("Seed skipped: users already exist.")
            return

        users = [
            User(
                name="Ava Carter",
                email="ava@example.com",
                subjects="Math, Physics",
                skill_level="Intermediate",
                availability="Mon 6PM, Wed 7PM",
            ),
            User(
                name="Liam Brooks",
                email="liam@example.com",
                subjects="Biology, Chemistry",
                skill_level="Beginner",
                availability="Tue 5PM, Thu 6PM",
            ),
            User(
                name="Noah Smith",
                email="noah@example.com",
                subjects="History, English",
                skill_level="Advanced",
                availability="Fri 4PM, Sat 10AM",
            ),
        ]

        for user in users:
            user.set_password("password123")
            db.session.add(user)

        db.session.flush()

        groups = [
            StudyGroup(
                subject="Math",
                description="Algebra and calculus problem-solving sessions.",
                schedule="Mon 6PM",
                max_members=6,
                creator_id=users[0].id,
                invite_token="math-pulse",
            ),
            StudyGroup(
                subject="Chemistry",
                description="Weekly chemistry fundamentals and quiz prep.",
                schedule="Thu 6PM",
                max_members=5,
                creator_id=users[1].id,
                invite_token="chem-lab-hub",
            ),
            StudyGroup(
                subject="History",
                description="Discuss key world history topics and essays.",
                schedule="Sat 10AM",
                max_members=4,
                creator_id=users[2].id,
                invite_token="history-circle",
            ),
        ]
        db.session.add_all(groups)
        db.session.flush()

        memberships = [
            GroupMember(user_id=users[0].id, group_id=groups[0].id, role="admin"),
            GroupMember(user_id=users[1].id, group_id=groups[1].id, role="admin"),
            GroupMember(user_id=users[2].id, group_id=groups[2].id, role="admin"),
            GroupMember(user_id=users[0].id, group_id=groups[1].id, role="moderator"),
        ]
        db.session.add_all(memberships)

        sessions = [
            GroupSession(
                group_id=groups[0].id,
                title="Algebra Drill",
                starts_at=datetime.utcnow() + timedelta(days=1),
                duration_minutes=75,
                notes="Focus on factorization and equations.",
            ),
            GroupSession(
                group_id=groups[1].id,
                title="Chemistry Quiz Prep",
                starts_at=datetime.utcnow() + timedelta(days=2),
                duration_minutes=60,
                notes="Acids, bases, and balancing reactions.",
            ),
            GroupSession(
                group_id=groups[2].id,
                title="Essay Review Circle",
                starts_at=datetime.utcnow() + timedelta(days=3),
                duration_minutes=90,
                notes="WWII causes and impact discussion.",
            ),
        ]
        db.session.add_all(sessions)

        db.session.add(
            Subscription(
                user_id=users[0].id,
                plan_type="premium",
                start_date=datetime.utcnow() - timedelta(days=2),
                end_date=datetime.utcnow() + timedelta(days=28),
                status="active",
            )
        )

        db.session.add(
            ChatMessage(
                group_id=groups[0].id,
                user_id=users[0].id,
                content="Welcome to the algebra drill. Share your toughest question.",
            )
        )
        db.session.commit()

        print("Sample data inserted.")

    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=app.config.get("DEBUG", False))
