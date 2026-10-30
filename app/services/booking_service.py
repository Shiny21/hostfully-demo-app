from sqlalchemy import select

from app.errors import BadRequestError, ConflictError, NotFoundError
from app.extensions import db
from app.models import Booking, BookingStatus
from app.repositories.availability import AvailabilityRepository
from app.schemas import BookingCreateSchema, BookingUpdateSchema


class BookingService:
    @staticmethod
    def create_booking(payload: dict) -> Booking:
        data = BookingCreateSchema.model_validate(payload)
        AvailabilityRepository.lock_and_get_property(data.property_id)
        AvailabilityRepository.assert_no_overlap(
            property_id=data.property_id,
            start_date=data.start_date,
            end_date=data.end_date,
        )
        booking = Booking(
            property_id=data.property_id,
            guest_name=data.guest_name,
            start_date=data.start_date,
            end_date=data.end_date,
            status=BookingStatus.CONFIRMED,
        )
        db.session.add(booking)
        db.session.commit()
        return booking

    @staticmethod
    def get_booking(booking_id: int) -> Booking:
        booking = db.session.get(Booking, booking_id)
        if not booking:
            raise NotFoundError(f"Booking with id {booking_id} was not found.")
        return booking

    @staticmethod
    def list_bookings(property_id: int | None = None, status: str | None = None) -> list[Booking]:
        stmt = select(Booking).order_by(Booking.start_date.asc(), Booking.id.asc())
        if property_id is not None:
            stmt = stmt.where(Booking.property_id == property_id)
        if status is not None:
            try:
                status_enum = BookingStatus(status.upper())
            except ValueError as exc:
                raise BadRequestError(f"Invalid status filter '{status}'.") from exc
            stmt = stmt.where(Booking.status == status_enum)
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def update_booking(booking_id: int, payload: dict) -> Booking:
        if not payload:
            raise BadRequestError("Update payload cannot be empty.")
        data = BookingUpdateSchema.model_validate(payload)
        booking = BookingService.get_booking(booking_id)
        AvailabilityRepository.lock_and_get_property(booking.property_id)

        new_start = data.start_date if data.start_date is not None else booking.start_date
        new_end = data.end_date if data.end_date is not None else booking.end_date
        if new_start >= new_end:
            raise BadRequestError("start_date must be strictly before end_date")

        if booking.status == BookingStatus.CONFIRMED:
            AvailabilityRepository.assert_no_overlap(
                property_id=booking.property_id,
                start_date=new_start,
                end_date=new_end,
                exclude_booking_id=booking.id,
            )

        if data.guest_name is not None:
            booking.guest_name = data.guest_name
        booking.start_date = new_start
        booking.end_date = new_end
        db.session.commit()
        return booking

    @staticmethod
    def cancel_booking(booking_id: int) -> Booking:
        booking = BookingService.get_booking(booking_id)
        booking.status = BookingStatus.CANCELED
        db.session.commit()
        return booking

    @staticmethod
    def rebook_booking(booking_id: int) -> Booking:
        booking = BookingService.get_booking(booking_id)
        if booking.status == BookingStatus.CONFIRMED:
            raise ConflictError(f"Booking {booking_id} is already CONFIRMED.")
        AvailabilityRepository.lock_and_get_property(booking.property_id)
        AvailabilityRepository.assert_no_overlap(
            property_id=booking.property_id,
            start_date=booking.start_date,
            end_date=booking.end_date,
            exclude_booking_id=booking.id,
        )
        booking.status = BookingStatus.CONFIRMED
        db.session.commit()
        return booking

    @staticmethod
    def delete_booking(booking_id: int) -> None:
        booking = BookingService.get_booking(booking_id)
        db.session.delete(booking)
        db.session.commit()
