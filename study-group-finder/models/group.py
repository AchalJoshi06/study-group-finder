from datetime import datetime
import secrets

from extensions import db


def _generate_invite_token():
    return secrets.token_urlsafe(9)


class StudyGroup(db.Model):
    __tablename__ = "study_group"
    __table_args__ = (
        db.CheckConstraint("max_members >= 2", name="ck_study_group_max_members_min"),
        db.CheckConstraint(
            "length(trim(subject)) > 0", name="ck_study_group_subject_not_blank"
        ),
        db.Index("ix_study_group_subject", "subject"),
    )

    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    schedule = db.Column(db.String(255), nullable=False)
    max_members = db.Column(db.Integer, nullable=False, default=5)
    is_private = db.Column(db.Boolean, nullable=False, default=False, index=True)
    invite_token = db.Column(db.String(64), nullable=False, unique=True, default=_generate_invite_token)
    creator_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship("User", back_populates="created_groups")
    members = db.relationship(
        "GroupMember", back_populates="group", cascade="all, delete-orphan"
    )
    sessions = db.relationship(
        "GroupSession", back_populates="group", cascade="all, delete-orphan"
    )
    chat_messages = db.relationship(
        "ChatMessage", back_populates="group", cascade="all, delete-orphan"
    )

    @property
    def current_member_count(self):
        return len(self.members)
