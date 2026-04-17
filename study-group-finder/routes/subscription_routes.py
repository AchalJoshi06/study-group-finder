from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from services.subscription_service import (
    activate_mock_premium_upgrade,
    get_active_subscription,
    get_usage_snapshot,
    is_premium,
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
    )


@subscription_bp.route("/upgrade", methods=["POST"])
@login_required
def upgrade():
    cycle = normalize_text(request.form.get("cycle", "monthly")).lower()
    if cycle not in {"monthly", "yearly"}:
        cycle = "monthly"

    activate_mock_premium_upgrade(current_user, cycle=cycle)
    flash("Premium plan activated successfully.", "success")
    return redirect(url_for("user.dashboard"))
