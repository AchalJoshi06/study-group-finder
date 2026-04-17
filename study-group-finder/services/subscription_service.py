from datetime import datetime, timedelta

from extensions import db
from models.group import StudyGroup
from models.membership import GroupMember
from models.subscription import Subscription


FREE_GROUP_CREATE_LIMIT = 3
FREE_GROUP_JOIN_LIMIT = 5


def get_active_subscription(user):
    now = datetime.utcnow()
    return (
        Subscription.query.filter(
            Subscription.user_id == user.id,
            Subscription.status == "active",
            Subscription.end_date > now,
        )
        .order_by(Subscription.end_date.desc(), Subscription.created_at.desc())
        .first()
    )


def is_premium(user):
    active_subscription = get_active_subscription(user)
    return bool(active_subscription and active_subscription.plan_type == "premium")


def can_create_group(user):
    if is_premium(user):
        return True

    created_count = StudyGroup.query.filter_by(creator_id=user.id).count()
    return created_count < FREE_GROUP_CREATE_LIMIT


def can_join_group(user):
    if is_premium(user):
        return True

    joined_count = GroupMember.query.filter_by(user_id=user.id).count()
    return joined_count < FREE_GROUP_JOIN_LIMIT


def get_plan_badge_label(user):
    return "Premium Plan" if is_premium(user) else "Free Plan"


def get_usage_snapshot(user):
    created_count = StudyGroup.query.filter_by(creator_id=user.id).count()
    joined_count = GroupMember.query.filter_by(user_id=user.id).count()

    return {
        "is_premium": is_premium(user),
        "created_count": created_count,
        "joined_count": joined_count,
        "create_limit": FREE_GROUP_CREATE_LIMIT,
        "join_limit": FREE_GROUP_JOIN_LIMIT,
    }


def activate_mock_premium_upgrade(user, cycle="monthly"):
    now = datetime.utcnow()

    Subscription.query.filter(
        Subscription.user_id == user.id,
        Subscription.status == "active",
    ).update({"status": "expired"}, synchronize_session=False)

    valid_days = 365 if cycle == "yearly" else 30
    subscription = Subscription(
        user_id=user.id,
        plan_type="premium",
        start_date=now,
        end_date=now + timedelta(days=valid_days),
        status="active",
        stripe_subscription_id=None,
    )
    db.session.add(subscription)
    db.session.commit()

    return subscription
