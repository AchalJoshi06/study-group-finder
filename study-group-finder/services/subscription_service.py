from datetime import datetime, timedelta
import os

from extensions import db
from models.group import StudyGroup
from models.membership import GroupMember
from models.subscription import Subscription


FREE_GROUP_CREATE_LIMIT = 3
FREE_GROUP_JOIN_LIMIT = 5


class SubscriptionServiceError(Exception):
    def __init__(self, message, category="warning"):
        super().__init__(message)
        self.category = category


def _get_stripe_module():
    try:
        import stripe
    except ImportError as exc:
        raise SubscriptionServiceError(
            "Billing provider is unavailable. Please contact support.",
            "danger",
        ) from exc

    return stripe


def _get_pricing_settings():
    return {
        "monthly_price_id": os.getenv("STRIPE_PRICE_MONTHLY_ID", ""),
        "yearly_price_id": os.getenv("STRIPE_PRICE_YEARLY_ID", ""),
        "monthly_price_display": os.getenv("PREMIUM_MONTHLY_PRICE", "$9.99"),
        "yearly_price_display": os.getenv("PREMIUM_YEARLY_PRICE", "$89.99"),
    }


def get_pricing_view_model():
    settings = _get_pricing_settings()
    billing_ready = bool(
        os.getenv("STRIPE_SECRET_KEY")
        and settings["monthly_price_id"]
        and settings["yearly_price_id"]
    )

    return {
        "monthly_price": settings["monthly_price_display"],
        "yearly_price": settings["yearly_price_display"],
        "billing_ready": billing_ready,
    }


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


def create_premium_checkout_session(user, cycle, success_url, cancel_url):
    if cycle not in {"monthly", "yearly"}:
        cycle = "monthly"

    settings = _get_pricing_settings()
    secret_key = os.getenv("STRIPE_SECRET_KEY")
    if not secret_key:
        raise SubscriptionServiceError(
            "Payments are not configured yet. Please try again later.",
            "warning",
        )

    price_id = (
        settings["yearly_price_id"] if cycle == "yearly" else settings["monthly_price_id"]
    )
    if not price_id:
        raise SubscriptionServiceError(
            "Selected billing plan is not configured. Please contact support.",
            "warning",
        )

    stripe = _get_stripe_module()
    stripe.api_key = secret_key

    try:
        checkout_session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            customer_email=user.email,
            metadata={"user_id": str(user.id), "cycle": cycle},
            success_url=f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=cancel_url,
            allow_promotion_codes=True,
        )
    except Exception as exc:
        raise SubscriptionServiceError(
            "Unable to start checkout. Please try again.",
            "danger",
        ) from exc

    return checkout_session


def _expire_user_active_subscriptions(user_id):
    Subscription.query.filter(
        Subscription.user_id == user_id,
        Subscription.status == "active",
    ).update({"status": "expired"}, synchronize_session=False)


def verify_payment_and_activate_premium(user, checkout_session_id):
    if not checkout_session_id:
        raise SubscriptionServiceError("Missing checkout session identifier.", "warning")

    secret_key = os.getenv("STRIPE_SECRET_KEY")
    if not secret_key:
        raise SubscriptionServiceError(
            "Payments are not configured yet. Please contact support.",
            "danger",
        )

    stripe = _get_stripe_module()
    stripe.api_key = secret_key

    try:
        checkout_session = stripe.checkout.Session.retrieve(
            checkout_session_id,
            expand=["subscription"],
        )
    except Exception as exc:
        raise SubscriptionServiceError(
            "Unable to verify checkout session.",
            "danger",
        ) from exc

    metadata = checkout_session.get("metadata") or {}
    session_user_id = metadata.get("user_id")
    customer_email = (checkout_session.get("customer_email") or "").lower()

    if session_user_id and session_user_id != str(user.id):
        raise SubscriptionServiceError(
            "Checkout session does not belong to the current user.",
            "danger",
        )

    if customer_email and customer_email != user.email.lower():
        raise SubscriptionServiceError(
            "Checkout session email does not match your account.",
            "danger",
        )

    if checkout_session.get("payment_status") != "paid":
        raise SubscriptionServiceError(
            "Payment is not verified yet. Complete payment to unlock Premium.",
            "warning",
        )

    stripe_subscription_id = checkout_session.get("subscription")
    if not stripe_subscription_id:
        raise SubscriptionServiceError(
            "Subscription information was not returned by the payment provider.",
            "danger",
        )

    existing = Subscription.query.filter_by(
        stripe_subscription_id=stripe_subscription_id,
        user_id=user.id,
        status="active",
    ).first()
    if existing and existing.end_date > datetime.utcnow():
        return existing

    try:
        subscription_obj = stripe.Subscription.retrieve(stripe_subscription_id)
    except Exception:
        subscription_obj = None

    if subscription_obj:
        start_ts = subscription_obj.get("current_period_start")
        end_ts = subscription_obj.get("current_period_end")
        start_date = datetime.utcfromtimestamp(start_ts) if start_ts else datetime.utcnow()
        end_date = datetime.utcfromtimestamp(end_ts) if end_ts else (datetime.utcnow() + timedelta(days=30))
    else:
        start_date = datetime.utcnow()
        end_date = datetime.utcnow() + timedelta(days=30)

    _expire_user_active_subscriptions(user.id)

    subscription = Subscription(
        user_id=user.id,
        plan_type="premium",
        start_date=start_date,
        end_date=end_date,
        status="active",
        stripe_subscription_id=stripe_subscription_id,
    )
    db.session.add(subscription)
    db.session.commit()

    return subscription
