import enum
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class BookingStatus(str, enum.Enum):
    CONFIRMED = "CONFIRMED"
    CANCELED = "CANCELED"


class Property(db.Model):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "country_code": self.country_code,
        }


class Booking(db.Model):
    __tablename__ = "bookings"
    __table_args__ = (
        Index("ix_bookings_prop_status_dates", "property_id", "status", "start_date", "end_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    property_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False
    )
    guest_name: Mapped[str] = mapped_column(String(120), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus), nullable=False, default=BookingStatus.CONFIRMED
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "property_id": self.property_id,
            "guest_name": self.guest_name,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "status": self.status.value,
        }


class Block(db.Model):
    __tablename__ = "blocks"
    __table_args__ = (
        Index("ix_blocks_prop_dates", "property_id", "start_date", "end_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    property_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "property_id": self.property_id,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
        }


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    api_key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "role": self.role}


class AuditEvent(db.Model):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    method: Mapped[str] = mapped_column(String(8), nullable=False)
    path: Mapped[str] = mapped_column(String(255), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "role": self.role,
            "method": self.method,
            "path": self.path,
            "status_code": self.status_code,
            "created_at": self.created_at.isoformat(),
        }
