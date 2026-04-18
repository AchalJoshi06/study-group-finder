from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from services.subscription_service import (
    SubscriptionServiceError,
    create_premium_checkout_session,
    get_active_subscription,
    get_pricing_view_model,
    get_usage_snapshot,
    is_premium,
    verify_payment_and_activate_premium,
)
from utils.validators import normalize_text


subscription_bp = Blueprint("subscription", __name__, url_prefix="/subscription")


@subscription_bp.route("/plans")
@login_required
def plans():
    return render_template(
        "subscription_plans.html",
        usage=get_usage_snapshot(current_user),
        active_subscription=get_active_subscription(current_user),
        is_premium_user=is_premium(current_user),
        pricing=get_pricing_view_model(),
    )


@subscription_bp.route("/upgrade", methods=["POST"])
@login_required
def upgrade():
    cycle = normalize_text(request.form.get("cycle", "monthly")).lower()
    if cycle not in {"monthly", "yearly"}:
        cycle = "monthly"

    success_url = url_for("subscription.checkout_success", _external=True)
    cancel_url = url_for("subscription.checkout_cancel", _external=True)

    try:
        checkout_session = create_premium_checkout_session(
            current_user,
            cycle=cycle,
            success_url=success_url,
            cancel_url=cancel_url,
        )
    except SubscriptionServiceError as exc:
        flash(str(exc), exc.category)
        return redirect(url_for("subscription.plans"))

    return redirect(checkout_session.url)


@subscription_bp.route("/checkout/success")
@login_required
def checkout_success():
    checkout_session_id = normalize_text(request.args.get("session_id"))

    try:
        verify_payment_and_activate_premium(current_user, checkout_session_id)
    except SubscriptionServiceError as exc:
        flash(str(exc), exc.category)
        return redirect(url_for("subscription.plans"))

    flash("Payment verified. Premium plan activated successfully.", "success")
    return redirect(url_for("user.dashboard"))


@subscription_bp.route("/checkout/cancel")
@login_required
def checkout_cancel():
    flash("Checkout was canceled. No payment was processed.", "info")
    return redirect(url_for("subscription.plans"))
