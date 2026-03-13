from functools import wraps
from flask import session, redirect, url_for, flash
from models.user_model import UserModel


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return UserModel.get_user_by_id(user_id)


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please login first.", "warning")
            return redirect(url_for("auth_bp.login"))
        return view_func(*args, **kwargs)
    return wrapper


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            flash("Please login first.", "warning")
            return redirect(url_for("auth_bp.login"))

        if not user.get("is_admin"):
            flash("Only admin can access that page.", "danger")
            return redirect(url_for("index"))

        return view_func(*args, **kwargs)
    return wrapper