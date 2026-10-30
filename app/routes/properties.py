from flask import Blueprint, jsonify, request
from sqlalchemy import select

from app.auth import require_role
from app.errors import BadRequestError, NotFoundError
from app.extensions import db
from app.models import Property
from app.schemas import PropertyCreateSchema

properties_bp = Blueprint("properties", __name__)


@properties_bp.post("")
@require_role("ADMIN", "MANAGER")
def create_property():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise BadRequestError("Request body must be a valid JSON object.")
    data = PropertyCreateSchema.model_validate(payload)
    prop = Property(name=data.name, country_code=data.country_code)
    db.session.add(prop)
    db.session.commit()
    return jsonify(prop.to_dict()), 201


@properties_bp.get("/<int:property_id>")
@require_role("ADMIN", "MANAGER", "GUEST")
def get_property(property_id: int):
    prop = db.session.get(Property, property_id)
    if not prop:
        raise NotFoundError(f"Property with id {property_id} was not found.")
    return jsonify(prop.to_dict()), 200


@properties_bp.get("")
@require_role("ADMIN", "MANAGER", "GUEST")
def list_properties():
    props = db.session.execute(select(Property).order_by(Property.id.asc())).scalars().all()
    return jsonify([p.to_dict() for p in props]), 200
