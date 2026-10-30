from flask import Blueprint, jsonify, request

from app.auth import require_role
from app.errors import BadRequestError
from app.services.booking_service import BookingService

bookings_bp = Blueprint("bookings", __name__)


@bookings_bp.post("")
@require_role("ADMIN", "MANAGER", "GUEST")
def create_booking():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise BadRequestError("Request body must be a valid JSON object.")
    booking = BookingService.create_booking(payload)
    return jsonify(booking.to_dict()), 201


@bookings_bp.get("/<int:booking_id>")
@require_role("ADMIN", "MANAGER", "GUEST")
def get_booking(booking_id: int):
    booking = BookingService.get_booking(booking_id)
    return jsonify(booking.to_dict()), 200


@bookings_bp.get("")
@require_role("ADMIN", "MANAGER", "GUEST")
def list_bookings():
    prop_id_raw = request.args.get("property_id")
    status = request.args.get("status")
    prop_id = None
    if prop_id_raw is not None:
        if not prop_id_raw.isdigit():
            raise BadRequestError("property_id query parameter must be an integer.")
        prop_id = int(prop_id_raw)
    bookings = BookingService.list_bookings(property_id=prop_id, status=status)
    return jsonify([b.to_dict() for b in bookings]), 200


@bookings_bp.route("/<int:booking_id>", methods=["PUT", "PATCH"])
@require_role("ADMIN", "MANAGER", "GUEST")
def update_booking(booking_id: int):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise BadRequestError("Request body must be a valid JSON object.")
    booking = BookingService.update_booking(booking_id, payload)
    return jsonify(booking.to_dict()), 200


@bookings_bp.post("/<int:booking_id>/cancel")
@require_role("ADMIN", "MANAGER", "GUEST")
def cancel_booking(booking_id: int):
    booking = BookingService.cancel_booking(booking_id)
    return jsonify(booking.to_dict()), 200


@bookings_bp.post("/<int:booking_id>/rebook")
@require_role("ADMIN", "MANAGER", "GUEST")
def rebook_booking(booking_id: int):
    booking = BookingService.rebook_booking(booking_id)
    return jsonify(booking.to_dict()), 200


@bookings_bp.delete("/<int:booking_id>")
@require_role("ADMIN", "MANAGER")
def delete_booking(booking_id: int):
    BookingService.delete_booking(booking_id)
    return "", 204
