from datetime import datetime, timezone
import traceback
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify

from models.user_model import UserModel
from models.slot_model import SlotModel
from models.reservation_model import ReservationModel
from utils.auth import login_required, get_current_user
from utils.aws_helpers import (
    publish_sns_notification,
    upload_text_receipt_to_s3,
    generate_presigned_file_url
)

try:
    from parking_availability_library.conflict_checker import has_booking_conflict
except ImportError:
    has_booking_conflict = None

try:
    from parking_availability_library.recommendation import recommend_best_slot
except ImportError:
    recommend_best_slot = None


reservation_bp = Blueprint("reservation_bp", __name__)


def _parse_datetime(datetime_str):
    """
    Parse datetime from HTML form and convert to UTC.
    """
    dt = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M")

    # Treat input as local time and convert to UTC
    local_dt = dt.astimezone()
    utc_dt = local_dt.astimezone(timezone.utc)

    return utc_dt


def _validate_reservation_inputs(user_id, slot_id, vehicle_number, reservation_start, reservation_end):
    if not user_id:
        return False, "User is required."
    if not slot_id:
        return False, "Parking slot is required."
    if not vehicle_number or not vehicle_number.strip():
        return False, "Vehicle number is required."
    if not reservation_start or not reservation_end:
        return False, "Reservation start and end time are required."

    try:
        user_id = int(user_id)
        slot_id = int(slot_id)
    except ValueError:
        return False, "Invalid user or slot value."

    user = UserModel.get_user_by_id(user_id)
    if not user:
        return False, "Selected user does not exist."

    slot = SlotModel.get_slot_by_id(slot_id)
    if not slot:
        return False, "Selected parking slot does not exist."

    if reservation_end <= reservation_start:
        return False, "Reservation end time must be after start time."

    return True, ""


def _check_conflict(slot_id, reservation_start, reservation_end, ignore_reservation_id=None):
    existing_reservations = ReservationModel.get_active_reservations_by_slot(slot_id)

    if ignore_reservation_id is not None:
        existing_reservations = [
            reservation
            for reservation in existing_reservations
            if reservation["id"] != ignore_reservation_id
        ]

    if has_booking_conflict:
        try:
            return has_booking_conflict(
                slot_id=slot_id,
                start_time=reservation_start,
                end_time=reservation_end,
                reservations=existing_reservations
            )
        except Exception:
            pass

    for reservation in existing_reservations:
        existing_start = reservation["reservation_start"]
        existing_end = reservation["reservation_end"]

        # Fix timezone mismatch
        if existing_start.tzinfo is None:
            existing_start = existing_start.replace(tzinfo=timezone.utc)

        if existing_end.tzinfo is None:
            existing_end = existing_end.replace(tzinfo=timezone.utc)

        overlap = not (
            reservation_end <= existing_start or
            reservation_start >= existing_end
        )

        if overlap:
            return True

    return False


def _admin_or_owner(booking, current_user):
    if not current_user:
        return False
    return current_user.get("is_admin") or booking["user_id"] == current_user["id"]

def _attach_display_status(bookings):
    """
    Add a live display_status field based on current time.
    This does not change the DB value; it only affects what is shown in the UI.
    """
    now = datetime.now(timezone.utc).astimezone()

    for booking in bookings:
        stored_status = str(booking.get("status", "")).lower()
        start_time = booking.get("reservation_start")
        end_time = booking.get("reservation_end")

        if stored_status in {"cancelled", "completed", "expired"}:
            booking["display_status"] = stored_status
        elif start_time and end_time:
            if now < start_time:
                booking["display_status"] = "reserved"
            elif start_time <= now <= end_time:
                booking["display_status"] = "active"
            else:
                booking["display_status"] = "expired"
        else:
            booking["display_status"] = stored_status or "reserved"

    return bookings

def _send_sns_safely(subject, message):
    """
    Try to send SNS notification without breaking the app flow.
    """
    try:
        response = publish_sns_notification(subject=subject, message=message)
        print(f"SNS publish successful: {response}")
    except Exception:
        print("SNS publish failed:")
        traceback.print_exc()


@reservation_bp.route("/reserve", methods=["GET", "POST"])
@login_required
def create_reservation():
    current_user = get_current_user()
    available_slots = SlotModel.get_available_slots()
    all_slots = SlotModel.get_all_slots()
    users = UserModel.get_all_users() if current_user.get("is_admin") else []
    recommended_slot = None

    if request.method == "POST":
        user_id = request.form.get("user_id") if current_user.get("is_admin") else current_user["id"]
        slot_id = request.form.get("slot_id")
        vehicle_number = request.form.get("vehicle_number", "").strip().upper()
        reservation_start_raw = request.form.get("reservation_start")
        reservation_end_raw = request.form.get("reservation_end")
        receipt_url = request.form.get("receipt_url", "").strip() or None

        try:
            reservation_start = _parse_datetime(reservation_start_raw)
            reservation_end = _parse_datetime(reservation_end_raw)
        except (ValueError, TypeError):
            flash("Invalid date/time format.", "danger")
            return render_template(
                "reserve.html",
                users=users,
                slots=available_slots,
                recommended_slot=recommended_slot
            )

        is_valid, error_message = _validate_reservation_inputs(
            user_id,
            slot_id,
            vehicle_number,
            reservation_start,
            reservation_end
        )
        if not is_valid:
            flash(error_message, "danger")
            return render_template(
                "reserve.html",
                users=users,
                slots=available_slots,
                recommended_slot=recommended_slot
            )

        user_id = int(user_id)
        slot_id = int(slot_id)

        if _check_conflict(slot_id, reservation_start, reservation_end):
            flash("Selected parking slot is already booked for that time range.", "danger")
            return render_template(
                "reserve.html",
                users=users,
                slots=available_slots,
                recommended_slot=recommended_slot
            )

        try:
            reservation = ReservationModel.create_reservation(
                user_id=user_id,
                slot_id=slot_id,
                vehicle_number=vehicle_number,
                reservation_start=reservation_start,
                reservation_end=reservation_end,
                status="reserved",
                receipt_url=receipt_url
            )

            if reservation:
                ReservationModel.log_notification(
                    reservation_id=reservation["id"],
                    message=f"Reservation created successfully for vehicle {vehicle_number}.",
                    channel="SNS"
                )

                try:
                    slot = SlotModel.get_slot_by_id(slot_id)
                    user = UserModel.get_user_by_id(user_id)

                    s3_key = upload_text_receipt_to_s3({
                        "reservation_id": reservation["id"],
                        "user_id": user_id,
                        "user_name": user["full_name"] if user else "",
                        "user_email": user["email"] if user else "",
                        "slot_id": slot_id,
                        "slot_number": slot["slot_number"] if slot else "",
                        "zone": slot["zone"] if slot else "",
                        "vehicle_number": vehicle_number,
                        "reservation_start": reservation_start,
                        "reservation_end": reservation_end,
                        "status": "reserved"
                    })

                    ReservationModel.update_receipt_url(reservation["id"], s3_key)
                except Exception as s3_error:
                    print(f"S3 receipt upload failed: {s3_error}")

                _send_sns_safely(
                    subject="Parking Reservation Created",
                    message=(
                        f"Reservation created successfully.\n\n"
                        f"Reservation ID: {reservation['id']}\n"
                        f"User ID: {user_id}\n"
                        f"Vehicle Number: {vehicle_number}\n"
                        f"Slot ID: {slot_id}\n"
                        f"Start Time: {reservation_start}\n"
                        f"End Time: {reservation_end}\n"
                        f"Status: reserved"
                    )
                )

                flash("Reservation created successfully.", "success")
                return redirect(url_for("reservation_bp.list_bookings"))

            flash("Unable to create reservation.", "danger")

        except Exception as exc:
            flash(f"Error creating reservation: {str(exc)}", "danger")

    preferred_zone = request.args.get("zone", "").strip()
    if recommend_best_slot and all_slots:
        try:
            recommended_slot = recommend_best_slot(
                slot_list=all_slots,
                vehicle_type="car",
                preferred_zone=preferred_zone or None
            )
        except Exception:
            recommended_slot = None

    return render_template(
        "reserve.html",
        users=users,
        slots=available_slots,
        recommended_slot=recommended_slot
    )


from datetime import timezone

@reservation_bp.route("/bookings", methods=["GET"])
@login_required
def list_bookings():
    current_user = get_current_user()

    if current_user.get("is_admin"):
        bookings = ReservationModel.get_all_reservations()
        page_title = "All Reservations"
    else:
        bookings = ReservationModel.get_reservations_by_user(current_user["id"])
        page_title = "My Reservations"

    # Convert UTC times to local timezone for display
    for booking in bookings:
        start_time = booking.get("reservation_start")
        end_time = booking.get("reservation_end")

        if start_time:
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
            booking["reservation_start"] = start_time.astimezone()

        if end_time:
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=timezone.utc)
            booking["reservation_end"] = end_time.astimezone()

        # Generate temporary S3 download URL if receipt exists
        if booking.get("receipt_url"):
            try:
                booking["receipt_download_url"] = generate_presigned_file_url(
                    booking["receipt_url"]
                )
            except Exception as s3_error:
                print(f"Presigned URL generation failed: {s3_error}")
                booking["receipt_download_url"] = None
        else:
            booking["receipt_download_url"] = None

    bookings = _attach_display_status(bookings)

    return render_template(
        "bookings.html",
        bookings=bookings,
        page_title=page_title,
        slot=None
    )


@reservation_bp.route("/api/dashboard", methods=["GET"])
def dashboard_data():
    """
    Returns real dashboard statistics and slot status
    """

    try:
        all_slots = SlotModel.get_all_slots()
        total_slots = len(all_slots)

        reservations = ReservationModel.get_all_reservations()

        available_slots = 0
        occupied_slots = 0
        reserved_slots = 0

        slot_status_map = {}

        # Determine slot status based on reservations
        current_time = datetime.now(timezone.utc)

        for reservation in reservations:

            slot_id = reservation["slot_id"]
            status = reservation.get("status")

            start = reservation.get("reservation_start")
            end = reservation.get("reservation_end")

            if start and start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)

            if end and end.tzinfo is None:
                end = end.replace(tzinfo=timezone.utc)

            if status == "reserved" and start <= current_time <= end:
                slot_status_map[slot_id] = "occupied"
            elif status == "reserved":
                slot_status_map[slot_id] = "reserved"

        slots_output = []

        for slot in all_slots:

            slot_id = slot["id"]
            slot_name = slot.get("slot_number") or f"Slot {slot_id}"

            status = slot_status_map.get(slot_id, "available")

            if status == "available":
                available_slots += 1
            elif status == "occupied":
                occupied_slots += 1
            elif status == "reserved":
                reserved_slots += 1

            slots_output.append({
                "name": slot_name,
                "status": status
            })

        return jsonify({
            "total_slots": total_slots,
            "available_slots": available_slots,
            "occupied_slots": occupied_slots,
            "reserved_slots": reserved_slots,
            "slots": slots_output
        })

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


@reservation_bp.route("/reservation/<int:reservation_id>", methods=["GET"])
@login_required
def reservation_details(reservation_id):
    current_user = get_current_user()
    booking = ReservationModel.get_reservation_by_id(reservation_id)
    if not booking:
        flash("Reservation not found.", "danger")
        return redirect(url_for("reservation_bp.list_bookings"))

    if not _admin_or_owner(booking, current_user):
        flash("Access denied.", "danger")
        return redirect(url_for("index"))
    
    bookings = _attach_display_status(bookings)

    return render_template(
        "bookings.html",
        bookings=[booking],
        page_title=f"Reservation #{reservation_id}",
        slot=None
    )


@reservation_bp.route("/reservation/edit/<int:reservation_id>", methods=["GET", "POST"])
@login_required
def edit_reservation(reservation_id):
    current_user = get_current_user()
    booking = ReservationModel.get_reservation_by_id(reservation_id)
    if not booking:
        flash("Reservation not found.", "danger")
        return redirect(url_for("reservation_bp.list_bookings"))

    if not _admin_or_owner(booking, current_user):
        flash("Access denied.", "danger")
        return redirect(url_for("index"))

    users = UserModel.get_all_users() if current_user.get("is_admin") else []
    all_slots = SlotModel.get_all_slots()

    if request.method == "POST":
        user_id = request.form.get("user_id") if current_user.get("is_admin") else current_user["id"]
        slot_id = request.form.get("slot_id")
        vehicle_number = request.form.get("vehicle_number", "").strip().upper()
        reservation_start_raw = request.form.get("reservation_start")
        reservation_end_raw = request.form.get("reservation_end")
        status = request.form.get("status", "reserved").strip().lower()
        receipt_url = request.form.get("receipt_url", "").strip() or None

        try:
            reservation_start = _parse_datetime(reservation_start_raw)
            reservation_end = _parse_datetime(reservation_end_raw)
        except (ValueError, TypeError):
            flash("Invalid date/time format.", "danger")
            return render_template(
                "edit_reservation.html",
                booking=booking,
                users=users,
                slots=all_slots
            )

        is_valid, error_message = _validate_reservation_inputs(
            user_id,
            slot_id,
            vehicle_number,
            reservation_start,
            reservation_end
        )
        if not is_valid:
            flash(error_message, "danger")
            return render_template(
                "edit_reservation.html",
                booking=booking,
                users=users,
                slots=all_slots
            )

        user_id = int(user_id)
        slot_id = int(slot_id)

        if status == "reserved" and _check_conflict(
            slot_id,
            reservation_start,
            reservation_end,
            ignore_reservation_id=reservation_id
        ):
            flash("Updated time conflicts with an existing reservation.", "danger")
            return render_template(
                "edit_reservation.html",
                booking=booking,
                users=users,
                slots=all_slots
            )

        try:
            updated = ReservationModel.update_reservation(
                reservation_id=reservation_id,
                user_id=user_id,
                slot_id=slot_id,
                vehicle_number=vehicle_number,
                reservation_start=reservation_start,
                reservation_end=reservation_end,
                status=status,
                receipt_url=receipt_url
            )

            if updated:
                ReservationModel.log_notification(
                    reservation_id=reservation_id,
                    message=f"Reservation #{reservation_id} updated successfully.",
                    channel="SNS"
                )

                try:
                    slot = SlotModel.get_slot_by_id(slot_id)
                    user = UserModel.get_user_by_id(user_id)

                    s3_key = upload_text_receipt_to_s3({
                        "reservation_id": reservation_id,
                        "user_id": user_id,
                        "user_name": user["full_name"] if user else "",
                        "user_email": user["email"] if user else "",
                        "slot_id": slot_id,
                        "slot_number": slot["slot_number"] if slot else "",
                        "zone": slot["zone"] if slot else "",
                        "vehicle_number": vehicle_number,
                        "reservation_start": reservation_start,
                        "reservation_end": reservation_end,
                        "status": status
                    })

                    ReservationModel.update_receipt_url(reservation_id, s3_key)
                except Exception as s3_error:
                    print(f"S3 receipt upload failed: {s3_error}")

                _send_sns_safely(
                    subject="Parking Reservation Updated",
                    message=(
                        f"Reservation updated successfully.\n\n"
                        f"Reservation ID: {reservation_id}\n"
                        f"User ID: {user_id}\n"
                        f"Vehicle Number: {vehicle_number}\n"
                        f"Slot ID: {slot_id}\n"
                        f"Start Time: {reservation_start}\n"
                        f"End Time: {reservation_end}\n"
                        f"Status: {status}"
                    )
                )

                flash("Reservation updated successfully.", "success")
                return redirect(url_for("reservation_bp.list_bookings"))

            flash("Unable to update reservation.", "danger")

        except Exception as exc:
            flash(f"Error updating reservation: {str(exc)}", "danger")

    return render_template(
        "edit_reservation.html",
        booking=booking,
        users=users,
        slots=all_slots
    )


@reservation_bp.route("/reservation/delete/<int:reservation_id>", methods=["POST", "GET"])
@login_required
def delete_reservation(reservation_id):
    current_user = get_current_user()
    booking = ReservationModel.get_reservation_by_id(reservation_id)
    if not booking:
        flash("Reservation not found.", "danger")
        return redirect(url_for("reservation_bp.list_bookings"))

    if not _admin_or_owner(booking, current_user):
        flash("Access denied.", "danger")
        return redirect(url_for("index"))

    try:
        ReservationModel.log_notification(
            reservation_id=booking["id"],
            message=f"Reservation #{reservation_id} deleted.",
            channel="SNS"
        )

        _send_sns_safely(
            subject="Parking Reservation Deleted",
            message=(
                f"Reservation deleted successfully.\n\n"
                f"Reservation ID: {reservation_id}\n"
                f"User ID: {booking['user_id']}\n"
                f"Vehicle Number: {booking['vehicle_number']}\n"
                f"Slot ID: {booking['slot_id']}\n"
                f"Status: deleted"
            )
        )

        deleted = ReservationModel.delete_reservation(reservation_id)
        flash(
            "Reservation deleted successfully." if deleted else "Unable to delete reservation.",
            "success" if deleted else "danger"
        )
    except Exception as exc:
        flash(f"Error deleting reservation: {str(exc)}", "danger")

    return redirect(url_for("reservation_bp.list_bookings"))


@reservation_bp.route("/reservation/cancel/<int:reservation_id>", methods=["POST", "GET"])
@login_required
def cancel_reservation(reservation_id):
    current_user = get_current_user()
    booking = ReservationModel.get_reservation_by_id(reservation_id)
    if not booking:
        flash("Reservation not found.", "danger")
        return redirect(url_for("reservation_bp.list_bookings"))

    if not _admin_or_owner(booking, current_user):
        flash("Access denied.", "danger")
        return redirect(url_for("index"))

    try:
        updated = ReservationModel.update_reservation_status(reservation_id, "cancelled")
        if updated:
            ReservationModel.log_notification(
                reservation_id=reservation_id,
                message=f"Reservation #{reservation_id} cancelled successfully.",
                channel="SNS"
            )

            _send_sns_safely(
                subject="Parking Reservation Cancelled",
                message=(
                    f"Reservation cancelled successfully.\n\n"
                    f"Reservation ID: {reservation_id}\n"
                    f"User ID: {booking['user_id']}\n"
                    f"Vehicle Number: {booking['vehicle_number']}\n"
                    f"Slot ID: {booking['slot_id']}\n"
                    f"Status: cancelled"
                )
            )

            flash("Reservation cancelled successfully.", "success")
        else:
            flash("Unable to cancel reservation.", "danger")
    except Exception as exc:
        flash(f"Error cancelling reservation: {str(exc)}", "danger")

    return redirect(url_for("reservation_bp.list_bookings"))