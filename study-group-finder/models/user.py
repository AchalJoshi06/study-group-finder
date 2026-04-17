from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "user"
    __table_args__ = (
        db.CheckConstraint(
            "skill_level IN ('Beginner', 'Intermediate', 'Advanced')",
            name="ck_user_skill_level",
        ),
        db.CheckConstraint("length(trim(name)) > 0", name="ck_user_name_not_blank"),
        db.Index("ix_user_email", "email"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    subjects = db.Column(db.Text, default="")
    skill_level = db.Column(db.String(50), default="Beginner")
    availability = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    memberships = db.relationship(
        "GroupMember", back_populates="user", cascade="all, delete-orphan"
    )
    created_groups = db.relationship("StudyGroup", back_populates="creator")
    subscriptions = db.relationship(
        "Subscription",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="Subscription.created_at.desc()",
    )
    chat_messages = db.relationship(
        "ChatMessage", back_populates="user", cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
