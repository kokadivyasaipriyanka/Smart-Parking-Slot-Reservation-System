from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.user_model import UserModel
from utils.auth import get_current_user


auth_bp = Blueprint("auth_bp", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    current_user = get_current_user()
    if current_user:
        return redirect(url_for("admin_bp.manage_slots" if current_user.get("is_admin") else "index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        user = UserModel.authenticate_user(email, password)
        if not user:
            flash("Invalid email or password.", "danger")
            return render_template("login.html")

        session["user_id"] = user["id"]
        session["user_name"] = user["full_name"]
        session["is_admin"] = bool(user.get("is_admin"))

        flash("Login successful.", "success")
        if user.get("is_admin"):
            return redirect(url_for("admin_bp.manage_slots"))
        return redirect(url_for("index"))

    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    current_user = get_current_user()
    if current_user:
        return redirect(url_for("index"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not full_name or not email or not password:
            flash("Full name, email, and password are required.", "danger")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        existing_user = UserModel.get_user_by_email(email)
        if existing_user:
            flash("Email already registered.", "danger")
            return render_template("register.html")

        UserModel.create_user(
            full_name=full_name,
            email=email,
            phone=phone,
            password=password,
            is_admin=False
        )

        flash("Registration successful. Please login.", "success")
        return redirect(url_for("auth_bp.login"))

    return render_template("register.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("auth_bp.login"))