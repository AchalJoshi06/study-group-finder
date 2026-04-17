from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from extensions import db
from models.group import StudyGroup
from services.group_service import get_upcoming_sessions_for_user
from services.subscription_service import get_usage_snapshot, is_premium
from utils.matcher import suggest_groups_for_user
from utils.validators import normalize_text


user_bp = Blueprint("user", __name__)


@user_bp.route("/dashboard")
@login_required
def dashboard():
    joined_memberships = list(current_user.memberships)
    joined_groups = [membership.group for membership in joined_memberships]
    joined_roles = {membership.group_id: membership.role for membership in joined_memberships}
    joined_group_ids = {group.id for group in joined_groups}

    all_groups = StudyGroup.query.order_by(StudyGroup.created_at.desc()).all()
    suggestions = suggest_groups_for_user(current_user, all_groups, joined_group_ids)
    upcoming_sessions = get_upcoming_sessions_for_user(current_user, limit=10)

    return render_template(
        "dashboard.html",
        joined_groups=joined_groups,
        joined_roles=joined_roles,
        suggestions=suggestions,
        upcoming_sessions=upcoming_sessions,
        is_premium_user=is_premium(current_user),
        usage_snapshot=get_usage_snapshot(current_user),
    )


@user_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        current_user.name = normalize_text(request.form.get("name"))
        current_user.subjects = normalize_text(request.form.get("subjects"))
        current_user.skill_level = normalize_text(request.form.get("skill_level"))
        current_user.availability = normalize_text(request.form.get("availability"))

        if not current_user.name:
            flash("Name is required.", "danger")
            return redirect(url_for("user.profile"))

        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("user.profile"))

    return render_template("profile.html")
