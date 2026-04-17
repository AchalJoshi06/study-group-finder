from datetime import datetime

from extensions import db


class GroupSession(db.Model):
    __tablename__ = "group_session"
    __table_args__ = (
        db.CheckConstraint(
            "duration_minutes >= 15", name="ck_group_session_duration_min"
        ),
        db.Index("ix_group_session_group_starts", "group_id", "starts_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("study_group.id"), nullable=False)
    title = db.Column(db.String(160), nullable=False)
    starts_at = db.Column(db.DateTime, nullable=False, index=True)
    duration_minutes = db.Column(db.Integer, nullable=False, default=60)
    notes = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    group = db.relationship("StudyGroup", back_populates="sessions")
