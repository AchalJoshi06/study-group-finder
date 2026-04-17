from datetime import datetime

from extensions import db


class ChatMessage(db.Model):
    __tablename__ = "chat_message"
    __table_args__ = (
        db.CheckConstraint("length(trim(content)) > 0", name="ck_chat_message_content_not_blank"),
        db.Index("ix_chat_message_group_created", "group_id", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("study_group.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    group = db.relationship("StudyGroup", back_populates="chat_messages")
    user = db.relationship("User", back_populates="chat_messages")
