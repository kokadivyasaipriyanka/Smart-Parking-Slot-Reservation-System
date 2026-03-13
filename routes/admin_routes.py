from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.slot_model import SlotModel
from models.reservation_model import ReservationModel
from models.user_model import UserModel
from utils.auth import admin_required


admin_bp = Blueprint("admin_bp", __name__, url_prefix="/admin")


@admin_bp.route("/slots", methods=["GET", "POST"])
@admin_required
def manage_slots():
    if request.method == "POST":
        slot_number = request.form.get("slot_number", "").strip().upper()
        zone = request.form.get("zone", "").strip()
        slot_type = request.form.get("slot_type", "").strip().lower()
        status = request.form.get("status", "available").strip().lower()

        if not slot_number or not zone or not slot_type:
            flash("Slot number, zone, and slot type are required.", "danger")
            slots = SlotModel.get_all_slots()
            return render_template("admin_slots.html", slots=slots)

        existing_slot = SlotModel.get_slot_by_number(slot_number)
        if existing_slot:
            flash("A slot with this slot number already exists.", "danger")
            slots = SlotModel.get_all_slots()
            return render_template("admin_slots.html", slots=slots)

        try:
            SlotModel.create_slot(
                slot_number=slot_number,
                zone=zone,
                slot_type=slot_type,
                status=status
            )
            flash("Parking slot created successfully.", "success")
            return redirect(url_for("admin_bp.manage_slots"))
        except Exception as exc:
            flash(f"Error creating slot: {str(exc)}", "danger")

    slots = SlotModel.get_all_slots()
    return render_template("admin_slots.html", slots=slots)


@admin_bp.route("/slots/edit/<int:slot_id>", methods=["GET", "POST"])
@admin_required
def edit_slot(slot_id):
    slot = SlotModel.get_slot_by_id(slot_id)
    if not slot:
        flash("Parking slot not found.", "danger")
        return redirect(url_for("admin_bp.manage_slots"))

    if request.method == "POST":
        slot_number = request.form.get("slot_number", "").strip().upper()
        zone = request.form.get("zone", "").strip()
        slot_type = request.form.get("slot_type", "").strip().lower()
        status = request.form.get("status", "available").strip().lower()

        if not slot_number or not zone or not slot_type:
            flash("Slot number, zone, and slot type are required.", "danger")
            slots = SlotModel.get_all_slots()
            return render_template("admin_slots.html", slots=slots, edit_slot=slot)

        existing_slot = SlotModel.get_slot_by_number(slot_number)
        if existing_slot and existing_slot["id"] != slot_id:
            flash("Another slot already uses this slot number.", "danger")
            slots = SlotModel.get_all_slots()
            return render_template("admin_slots.html", slots=slots, edit_slot=slot)

        try:
            SlotModel.update_slot(
                slot_id=slot_id,
                slot_number=slot_number,
                zone=zone,
                slot_type=slot_type,
                status=status
            )
            flash("Parking slot updated successfully.", "success")
            return redirect(url_for("admin_bp.manage_slots"))
        except Exception as exc:
            flash(f"Error updating slot: {str(exc)}", "danger")

    slots = SlotModel.get_all_slots()
    return render_template("admin_slots.html", slots=slots, edit_slot=slot)


@admin_bp.route("/slots/delete/<int:slot_id>", methods=["POST", "GET"])
@admin_required
def delete_slot(slot_id):
    slot = SlotModel.get_slot_by_id(slot_id)
    if not slot:
        flash("Parking slot not found.", "danger")
        return redirect(url_for("admin_bp.manage_slots"))

    active_reservations = ReservationModel.get_active_reservations_by_slot(slot_id)
    if active_reservations:
        flash("Cannot delete slot because it has active reservations.", "danger")
        return redirect(url_for("admin_bp.manage_slots"))

    try:
        deleted = SlotModel.delete_slot(slot_id)
        if deleted:
            flash("Parking slot deleted successfully.", "success")
        else:
            flash("Unable to delete parking slot.", "danger")
    except Exception as exc:
        flash(f"Error deleting slot: {str(exc)}", "danger")

    return redirect(url_for("admin_bp.manage_slots"))


@admin_bp.route("/slots/status/<int:slot_id>", methods=["POST"])
@admin_required
def update_slot_status(slot_id):
    slot = SlotModel.get_slot_by_id(slot_id)
    if not slot:
        flash("Parking slot not found.", "danger")
        return redirect(url_for("admin_bp.manage_slots"))

    status = request.form.get("status", "").strip().lower()
    if not status:
        flash("Status is required.", "danger")
        return redirect(url_for("admin_bp.manage_slots"))

    try:
        SlotModel.update_slot_status(slot_id, status)
        flash("Slot status updated successfully.", "success")
    except Exception as exc:
        flash(f"Error updating slot status: {str(exc)}", "danger")

    return redirect(url_for("admin_bp.manage_slots"))


@admin_bp.route("/users", methods=["GET", "POST"])
@admin_required
def manage_users():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "").strip()
        is_admin = request.form.get("is_admin") == "on"

        if not full_name or not email or not password:
            flash("Full name, email, and password are required.", "danger")
            users = UserModel.get_all_users()
            return render_template("admin_users.html", users=users)

        if UserModel.get_user_by_email(email):
            flash("Email already exists.", "danger")
            users = UserModel.get_all_users()
            return render_template("admin_users.html", users=users)

        UserModel.create_user(
            full_name=full_name,
            email=email,
            phone=phone,
            password=password,
            is_admin=is_admin
        )
        flash("User created successfully.", "success")
        return redirect(url_for("admin_bp.manage_users"))

    users = UserModel.get_all_users()
    return render_template("admin_users.html", users=users)


@admin_bp.route("/users/edit/<int:user_id>", methods=["GET", "POST"])
@admin_required
def edit_user(user_id):
    user = UserModel.get_user_by_id(user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("admin_bp.manage_users"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "").strip() or None
        is_admin = request.form.get("is_admin") == "on"

        existing_user = UserModel.get_user_by_email(email)
        if existing_user and existing_user["id"] != user_id:
            flash("Another user already uses this email.", "danger")
            users = UserModel.get_all_users()
            return render_template("admin_users.html", users=users, edit_user=user)

        UserModel.update_user(
            user_id=user_id,
            full_name=full_name,
            email=email,
            phone=phone,
            password=password,
            is_admin=is_admin
        )
        flash("User updated successfully.", "success")
        return redirect(url_for("admin_bp.manage_users"))

    users = UserModel.get_all_users()
    return render_template("admin_users.html", users=users, edit_user=user)


@admin_bp.route("/users/delete/<int:user_id>", methods=["POST", "GET"])
@admin_required
def delete_user(user_id):
    if session.get("user_id") == user_id:
        flash("You cannot delete your own logged-in admin account.", "danger")
        return redirect(url_for("admin_bp.manage_users"))

    user = UserModel.get_user_by_id(user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("admin_bp.manage_users"))

    UserModel.delete_user(user_id)
    flash("User deleted successfully.", "success")
    return redirect(url_for("admin_bp.manage_users"))