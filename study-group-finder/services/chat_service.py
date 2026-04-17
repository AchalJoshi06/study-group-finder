from extensions import db
from models.chat_message import ChatMessage
from models.membership import GroupMember


class ChatServiceError(Exception):
    def __init__(self, message, category="warning"):
        super().__init__(message)
        self.category = category


def _is_member(user_id, group_id):
    return GroupMember.query.filter_by(user_id=user_id, group_id=group_id).first() is not None


def get_group_messages(group_id, limit=120):
    return (
        ChatMessage.query.filter_by(group_id=group_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
        .all()
    )


def post_message(user, group, content):
    cleaned_content = (content or "").strip()
    if not cleaned_content:
        raise ChatServiceError("Message cannot be empty.", "warning")

    if len(cleaned_content) > 800:
        raise ChatServiceError("Message is too long. Keep it under 800 characters.", "warning")

    if not _is_member(user.id, group.id):
        raise ChatServiceError("Join this group to access chat.", "warning")

    message = ChatMessage(group_id=group.id, user_id=user.id, content=cleaned_content)
    db.session.add(message)
    db.session.commit()
    return message
