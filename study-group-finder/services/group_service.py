from datetime import datetime, timedelta

from extensions import db
from models.chat_message import ChatMessage
from models.group import StudyGroup
from models.membership import GroupMember
from models.session import GroupSession
from models.user import User
from services.subscription_service import can_create_group, can_join_group, is_premium


class GroupServiceError(Exception):
    def __init__(self, message, category="warning", redirect_endpoint=None):
        super().__init__(message)
        self.category = category
        self.redirect_endpoint = redirect_endpoint


def _parse_max_members(raw_value, fallback=5):
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return fallback


def _membership_lookup(user_id, group_id):
    return GroupMember.query.filter_by(user_id=user_id, group_id=group_id).first()


def get_user_role_in_group(user, group):
    membership = _membership_lookup(user.id, group.id)
    return membership.role if membership else None


def get_filtered_groups(user, subject_filter="", time_filter="", creator_filter=""):
    query = StudyGroup.query.filter_by(is_private=False)

    if subject_filter:
        query = query.filter(StudyGroup.subject.ilike(f"%{subject_filter}%"))
    if time_filter:
        query = query.filter(StudyGroup.schedule.ilike(f"%{time_filter}%"))

    if creator_filter:
        if not is_premium(user):
            raise GroupServiceError(
                "Upgrade required to access this feature",
                "warning",
                redirect_endpoint="subscription.plans",
            )
        query = query.join(User, User.id == StudyGroup.creator_id).filter(
            User.name.ilike(f"%{creator_filter}%")
        )

    return query.order_by(StudyGroup.created_at.desc()).all()


def get_joined_group_ids(user):
    return {membership.group_id for membership in user.memberships}


def create_study_group(user, subject, description, schedule, max_members_raw, is_private=False):
    max_members = _parse_max_members(max_members_raw)

    if not subject or not description or not schedule:
        raise GroupServiceError("Please fill in all fields.", "danger")

    if max_members < 2:
        raise GroupServiceError("Max members must be at least 2.", "warning")

    if is_private and not is_premium(user):
        raise GroupServiceError(
            "Upgrade required to access this feature",
            "warning",
            redirect_endpoint="subscription.plans",
        )

    if not can_create_group(user):
        raise GroupServiceError(
            "Free limit reached. Upgrade to create more groups.",
            "warning",
            redirect_endpoint="subscription.plans",
        )

    group = StudyGroup(
        subject=subject,
        description=description,
        schedule=schedule,
        max_members=max_members,
        creator_id=user.id,
        is_private=is_private,
    )
    db.session.add(group)
    db.session.flush()

    db.session.add(GroupMember(user_id=user.id, group_id=group.id, role="admin"))
    db.session.commit()

    return group


def join_study_group(user, group, allow_private=False):
    existing = _membership_lookup(user.id, group.id)
    if existing:
        raise GroupServiceError("You are already in this group.", "info")

    if group.is_private and not allow_private:
        raise GroupServiceError("Private groups can only be joined via invite link.", "warning")

    if group.current_member_count >= group.max_members:
        raise GroupServiceError("This group is full.", "warning")

    if not can_join_group(user):
        raise GroupServiceError(
            "Free limit reached. Upgrade to join more groups.",
            "warning",
            redirect_endpoint="subscription.plans",
        )

    db.session.add(GroupMember(user_id=user.id, group_id=group.id, role="member"))
    db.session.commit()


def leave_study_group(user, group, transfer_user_id=None):
    membership = _membership_lookup(user.id, group.id)
    if not membership:
        raise GroupServiceError("You are not a member of this group.", "warning")

    if group.creator_id == user.id:
        if transfer_user_id is None:
            raise GroupServiceError(
                "Transfer ownership before leaving your own group.",
                "warning",
            )

        if transfer_user_id == user.id:
            raise GroupServiceError("Choose a different member to transfer ownership.", "warning")

        new_admin = _membership_lookup(transfer_user_id, group.id)
        if not new_admin:
            raise GroupServiceError(
                "Selected user is not a member of this group.",
                "warning",
            )

        group.creator_id = transfer_user_id
        new_admin.role = "admin"

    db.session.delete(membership)
    db.session.commit()


def get_upcoming_sessions_for_user(user, limit=8):
    joined_group_ids = get_joined_group_ids(user)
    if not joined_group_ids:
        return []

    now = datetime.utcnow()
    return (
        GroupSession.query.filter(
            GroupSession.group_id.in_(joined_group_ids),
            GroupSession.starts_at >= now,
        )
        .order_by(GroupSession.starts_at.asc())
        .limit(limit)
        .all()
    )


def get_group_memberships(group):
    return GroupMember.query.filter_by(group_id=group.id).order_by(GroupMember.joined_at.asc()).all()


def ensure_group_admin(user, group):
    role = get_user_role_in_group(user, group)
    if role != "admin":
        raise GroupServiceError("Only group admins can manage this group.", "warning")


def set_group_member_role(admin_user, group, target_user_id, new_role):
    ensure_group_admin(admin_user, group)

    if new_role not in {"admin", "moderator", "member"}:
        raise GroupServiceError("Invalid role selected.", "warning")

    target_membership = _membership_lookup(target_user_id, group.id)
    if not target_membership:
        raise GroupServiceError("Selected member is not in this group.", "warning")

    if target_user_id == group.creator_id and new_role != "admin":
        raise GroupServiceError("Group creator must remain admin.", "warning")

    target_membership.role = new_role
    db.session.commit()


def remove_group_member(admin_user, group, target_user_id):
    ensure_group_admin(admin_user, group)

    target_membership = _membership_lookup(target_user_id, group.id)
    if not target_membership:
        raise GroupServiceError("Selected member is not in this group.", "warning")

    if target_user_id == group.creator_id:
        raise GroupServiceError("Creator cannot be removed from the group.", "warning")

    db.session.delete(target_membership)
    db.session.commit()


def get_group_analytics(group):
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    total_members = GroupMember.query.filter_by(group_id=group.id).count()
    joins_last_7_days = GroupMember.query.filter(
        GroupMember.group_id == group.id,
        GroupMember.joined_at >= seven_days_ago,
    ).count()

    session_activity_count = GroupSession.query.filter_by(group_id=group.id).count()
    message_activity_count = ChatMessage.query.filter_by(group_id=group.id).count()

    return {
        "total_members": total_members,
        "joins_last_7_days": joins_last_7_days,
        "activity_count": session_activity_count + message_activity_count,
        "session_activity_count": session_activity_count,
        "message_activity_count": message_activity_count,
    }
