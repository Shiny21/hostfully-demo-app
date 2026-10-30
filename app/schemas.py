from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class PropertyCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=120)
    country_code: str = Field(..., min_length=2, max_length=2)

    @field_validator("country_code")
    @classmethod
    def validate_country_code(cls, v: str) -> str:
        if not v.isascii() or not v.isalpha():
            raise ValueError("country_code must consist of 2 ASCII letters")
        return v.upper()


class DateRangeMixin(BaseModel):
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def check_start_before_end(self):
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be strictly before end_date")
        return self


class BookingCreateSchema(DateRangeMixin):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    property_id: int = Field(..., gt=0)
    guest_name: str = Field(..., min_length=1, max_length=120)


class BookingUpdateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    guest_name: str | None = Field(default=None, min_length=1, max_length=120)
    start_date: date | None = None
    end_date: date | None = None


class BlockCreateSchema(DateRangeMixin):
    model_config = ConfigDict(extra="forbid")

    property_id: int = Field(..., gt=0)


class BlockUpdateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_date: date | None = None
    end_date: date | None = None


class UserCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=120)
    role: Literal["ADMIN", "MANAGER", "GUEST"]


class UserUpdateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=120)
    role: Literal["ADMIN", "MANAGER", "GUEST"] | None = None
