from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user

from services.subscription_service import is_premium


def premium_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))

        if not is_premium(current_user):
            flash("Upgrade required to access this feature", "warning")
            return redirect(url_for("subscription.plans"))

        return view_func(*args, **kwargs)

    return wrapped_view
