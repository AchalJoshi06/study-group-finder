from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.group import StudyGroup
from services.chat_service import ChatServiceError, get_group_messages, post_message
from services.group_service import get_user_role_in_group
from utils.decorators import premium_required
from utils.validators import normalize_text


chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


@chat_bp.route("/<int:group_id>", methods=["GET", "POST"])
@login_required
@premium_required
def group_chat(group_id):
    group = StudyGroup.query.get_or_404(group_id)
    role = get_user_role_in_group(current_user, group)
    if not role:
        flash("Join this group to access chat.", "warning")
        return redirect(url_for("group.browse_groups"))

    if request.method == "POST":
        try:
            post_message(current_user, group, normalize_text(request.form.get("content")))
        except ChatServiceError as exc:
            flash(str(exc), exc.category)
        return redirect(url_for("chat.group_chat", group_id=group.id))

    return render_template(
        "group_chat.html",
        group=group,
        role=role,
        messages=get_group_messages(group.id),
    )
