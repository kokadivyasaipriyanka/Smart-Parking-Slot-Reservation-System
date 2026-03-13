from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.slot_model import SlotModel
from models.reservation_model import ReservationModel

try:
    from parking_availability_library.availability import get_currently_available_slots
except ImportError:
    get_currently_available_slots = None


slot_bp = Blueprint("slot_bp", __name__)


@slot_bp.route("/slots", methods=["GET"])
def list_slots():
    """
    Display all parking slots with optional filtering by zone and status.
    """
    zone = request.args.get("zone", "").strip()
    status = request.args.get("status", "").strip()

    if zone and status:
        all_slots = SlotModel.get_slots_by_zone(zone)
        slots = [slot for slot in all_slots if slot["status"] == status]
    elif zone:
        slots = SlotModel.get_slots_by_zone(zone)
    elif status:
        slots = SlotModel.get_slots_by_status(status)
    else:
        slots = SlotModel.get_all_slots()

    all_slots = SlotModel.get_all_slots()
    unique_zones = sorted({slot["zone"] for slot in all_slots})
    unique_statuses = ["available", "reserved", "occupied", "maintenance"]

    return render_template(
        "slots.html",
        slots=slots,
        unique_zones=unique_zones,
        unique_statuses=unique_statuses,
        selected_zone=zone,
        selected_status=status
    )


@slot_bp.route("/available-slots", methods=["GET"])
def available_slots():
    """
    Show currently available slots.
    If the custom library function exists, use it.
    Otherwise, fall back to DB status='available'.
    """
    slots = SlotModel.get_all_slots()
    active_reservations = [
        reservation
        for reservation in ReservationModel.get_all_reservations()
        if reservation["status"] == "reserved"
    ]

    if get_currently_available_slots:
        try:
            available = get_currently_available_slots(slots, active_reservations)
        except Exception:
            available = SlotModel.get_available_slots()
    else:
        available = SlotModel.get_available_slots()

    return render_template(
        "slots.html",
        slots=available,
        unique_zones=[],
        unique_statuses=["available"],
        selected_zone="",
        selected_status="available"
    )


@slot_bp.route("/slots/<int:slot_id>", methods=["GET"])
def slot_details(slot_id):
    """
    Redirect-based details handler.
    Since no separate detail template exists in your structure,
    this route highlights slot-related reservations in bookings page.
    """
    slot = SlotModel.get_slot_by_id(slot_id)
    if not slot:
        flash("Parking slot not found.", "danger")
        return redirect(url_for("slot_bp.list_slots"))

    reservations = ReservationModel.get_reservations_by_slot(slot_id)

    return render_template(
        "bookings.html",
        bookings=reservations,
        page_title=f"Reservations for Slot {slot['slot_number']}",
        slot=slot
    )