from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.group import StudyGroup
from services.group_service import (
    GroupServiceError,
    create_study_group,
    get_filtered_groups,
    get_group_analytics,
    get_group_memberships,
    get_joined_group_ids,
    get_user_role_in_group,
    join_study_group,
    leave_study_group,
    remove_group_member,
    set_group_member_role,
)
from services.subscription_service import is_premium
from utils.decorators import premium_required
from utils.validators import normalize_text


group_bp = Blueprint("group", __name__, url_prefix="/groups")


@group_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_group():
    if request.method == "POST":
        subject = normalize_text(request.form.get("subject"))
        description = normalize_text(request.form.get("description"))
        schedule = normalize_text(request.form.get("schedule"))
        is_private = request.form.get("is_private") == "on"

        try:
            create_study_group(
                current_user,
                subject,
                description,
                schedule,
                request.form.get("max_members", 5),
                is_private=is_private,
            )
        except GroupServiceError as exc:
            flash(str(exc), exc.category)
            if exc.redirect_endpoint:
                return redirect(url_for(exc.redirect_endpoint))
            return render_template("create_group.html", is_premium_user=is_premium(current_user))

        flash("Group created successfully.", "success")
        return redirect(url_for("group.browse_groups"))

    return render_template("create_group.html", is_premium_user=is_premium(current_user))


@group_bp.route("/browse")
@login_required
def browse_groups():
    subject_filter = normalize_text(request.args.get("subject"))
    time_filter = normalize_text(request.args.get("time"))
    creator_filter = normalize_text(request.args.get("creator"))

    try:
        groups = get_filtered_groups(current_user, subject_filter, time_filter, creator_filter)
    except GroupServiceError as exc:
        flash(str(exc), exc.category)
        if exc.redirect_endpoint:
            return redirect(url_for(exc.redirect_endpoint))
        return redirect(url_for("group.browse_groups"))

    joined_group_ids = get_joined_group_ids(current_user)
    joined_roles = {membership.group_id: membership.role for membership in current_user.memberships}

    return render_template(
        "browse_groups.html",
        groups=groups,
        joined_group_ids=joined_group_ids,
        joined_roles=joined_roles,
        subject_filter=subject_filter,
        time_filter=time_filter,
        creator_filter=creator_filter,
        is_premium_user=is_premium(current_user),
    )


@group_bp.route("/<int:group_id>/join", methods=["POST"])
@login_required
def join_group(group_id):
    group = StudyGroup.query.get_or_404(group_id)
    try:
        join_study_group(current_user, group, allow_private=False)
    except GroupServiceError as exc:
        flash(str(exc), exc.category)
        if exc.redirect_endpoint:
            return redirect(url_for(exc.redirect_endpoint))
        return redirect(url_for("group.browse_groups"))

    flash("You joined the group.", "success")
    return redirect(url_for("group.browse_groups"))


@group_bp.route("/invite/<string:invite_token>")
@login_required
def join_group_by_invite(invite_token):
    group = StudyGroup.query.filter_by(invite_token=invite_token).first_or_404()

    try:
        join_study_group(current_user, group, allow_private=True)
    except GroupServiceError as exc:
        flash(str(exc), exc.category)
        if exc.redirect_endpoint:
            return redirect(url_for(exc.redirect_endpoint))
        return redirect(url_for("group.browse_groups"))

    flash("Invite accepted. You joined the group.", "success")
    return redirect(url_for("group.browse_groups"))


@group_bp.route("/<int:group_id>/leave", methods=["POST"])
@login_required
def leave_group(group_id):
    group = StudyGroup.query.get_or_404(group_id)
    transfer_raw = normalize_text(request.form.get("transfer_user_id"))

    transfer_user_id = None
    if transfer_raw:
        try:
            transfer_user_id = int(transfer_raw)
        except ValueError:
            flash("Invalid transfer member selection.", "warning")
            return redirect(url_for("group.browse_groups"))

    try:
        leave_study_group(current_user, group, transfer_user_id=transfer_user_id)
    except GroupServiceError as exc:
        flash(str(exc), exc.category)
        if exc.redirect_endpoint:
            return redirect(url_for(exc.redirect_endpoint))
        return redirect(url_for("group.browse_groups"))

    flash("You left the group.", "info")
    return redirect(url_for("group.browse_groups"))


@group_bp.route("/<int:group_id>/analytics")
@login_required
@premium_required
def group_analytics(group_id):
    group = StudyGroup.query.get_or_404(group_id)
    role = get_user_role_in_group(current_user, group)
    if not role:
        flash("Join this group to view analytics.", "warning")
        return redirect(url_for("group.browse_groups"))

    return render_template(
        "group_analytics.html",
        group=group,
        role=role,
        analytics=get_group_analytics(group),
    )


@group_bp.route("/<int:group_id>/manage", methods=["GET", "POST"])
@login_required
def manage_group(group_id):
    group = StudyGroup.query.get_or_404(group_id)
    role = get_user_role_in_group(current_user, group)
    if role != "admin":
        flash("Only group admins can manage this group.", "warning")
        return redirect(url_for("group.browse_groups"))

    if request.method == "POST":
        action = normalize_text(request.form.get("action"))
        target_user_raw = normalize_text(request.form.get("target_user_id"))

        try:
            target_user_id = int(target_user_raw)
        except ValueError:
            flash("Invalid member selection.", "warning")
            return redirect(url_for("group.manage_group", group_id=group.id))

        try:
            if action == "set_role":
                new_role = normalize_text(request.form.get("new_role"))
                set_group_member_role(current_user, group, target_user_id, new_role)
                flash("Member role updated.", "success")
            elif action == "remove_member":
                remove_group_member(current_user, group, target_user_id)
                flash("Member removed from group.", "info")
            else:
                flash("Unsupported action.", "warning")
        except GroupServiceError as exc:
            flash(str(exc), exc.category)

        return redirect(url_for("group.manage_group", group_id=group.id))

    memberships = get_group_memberships(group)
    return render_template(
        "group_manage.html",
        group=group,
        memberships=memberships,
    )
