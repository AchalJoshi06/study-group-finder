from datetime import datetime

from extensions import db


class GroupMember(db.Model):
    __tablename__ = "group_member"
    __table_args__ = (
        db.CheckConstraint("role IN ('admin', 'moderator', 'member')", name="ck_group_member_role"),
        db.Index("ix_group_member_group_role", "group_id", "role"),
    )

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("study_group.id"), primary_key=True)
    role = db.Column(db.String(20), nullable=False, default="member")
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="memberships")
    group = db.relationship("StudyGroup", back_populates="members")
