from datetime import date

from sqlalchemy import select

from app.errors import ConflictError, NotFoundError
from app.extensions import db
from app.models import Block, Booking, BookingStatus, Property


def ranges_overlap_inclusive(
    start_a: date, end_a: date, start_b: date, end_b: date
) -> bool:
    return start_a <= end_b and end_a >= start_b


class AvailabilityRepository:
    @staticmethod
    def lock_and_get_property(property_id: int) -> Property:
        stmt = select(Property).where(Property.id == property_id).with_for_update()
        prop = db.session.execute(stmt).scalar_one_or_none()
        if not prop:
            raise NotFoundError(f"Property with id {property_id} was not found.")
        return prop

    @staticmethod
    def assert_no_overlap(
        property_id: int,
        start_date: date,
        end_date: date,
        exclude_booking_id: int | None = None,
        exclude_block_id: int | None = None,
    ) -> None:
        booking_stmt = select(Booking).where(
            Booking.property_id == property_id,
            Booking.status == BookingStatus.CONFIRMED,
            Booking.start_date <= end_date,
            Booking.end_date >= start_date,
        )
        if exclude_booking_id is not None:
            booking_stmt = booking_stmt.where(Booking.id != exclude_booking_id)

        conflicting_booking = db.session.execute(booking_stmt).scalars().first()
        if conflicting_booking:
            raise ConflictError(
                f"Dates {start_date} to {end_date} overlap with existing confirmed booking "
                f"(id={conflicting_booking.id})."
            )

        block_stmt = select(Block).where(
            Block.property_id == property_id,
            Block.start_date <= end_date,
            Block.end_date >= start_date,
        )
        if exclude_block_id is not None:
            block_stmt = block_stmt.where(Block.id != exclude_block_id)

        conflicting_block = db.session.execute(block_stmt).scalars().first()
        if conflicting_block:
            raise ConflictError(
                f"Dates {start_date} to {end_date} overlap with an existing block "
                f"(id={conflicting_block.id})."
            )
