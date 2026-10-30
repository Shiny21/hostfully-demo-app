import hashlib
import secrets

from flask import Blueprint, jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.auth import require_role
from app.errors import BadRequestError, ConflictError, NotFoundError
from app.extensions import db
from app.models import AuditEvent, User
from app.schemas import UserCreateSchema, UserUpdateSchema

admin_api_bp = Blueprint("admin_api", __name__)


def get_user(user_id: int) -> User:
    user = db.session.get(User, user_id)
    if user is None:
        raise NotFoundError(f"User with id {user_id} was not found.")
    return user


def commit_user() -> None:
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ConflictError("A user with that name already exists.") from exc


@admin_api_bp.get("/users")
@require_role("ADMIN")
def list_users():
    users = db.session.execute(select(User).order_by(User.id)).scalars().all()
    return jsonify([user.to_dict() for user in users]), 200


@admin_api_bp.post("/users")
@require_role("ADMIN")
def create_user():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise BadRequestError("Request body must be a valid JSON object.")
    data = UserCreateSchema.model_validate(payload)
    api_key = secrets.token_urlsafe(24)
    user = User(
        name=data.name,
        role=data.role,
        api_key_hash=hashlib.sha256(api_key.encode()).hexdigest(),
    )
    db.session.add(user)
    commit_user()
    return jsonify({**user.to_dict(), "api_key": api_key}), 201


@admin_api_bp.patch("/users/<int:user_id>")
@require_role("ADMIN")
def update_user(user_id: int):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not payload:
        raise BadRequestError("Request body must be a non-empty JSON object.")
    data = UserUpdateSchema.model_validate(payload)
    user = get_user(user_id)
    if data.name is not None:
        user.name = data.name
    if data.role is not None:
        user.role = data.role
    commit_user()
    return jsonify(user.to_dict()), 200


@admin_api_bp.delete("/users/<int:user_id>")
@require_role("ADMIN")
def delete_user(user_id: int):
    db.session.delete(get_user(user_id))
    db.session.commit()
    return "", 204


@admin_api_bp.get("/audit")
@require_role("ADMIN")
def list_audit_events():
    events = db.session.execute(select(AuditEvent).order_by(AuditEvent.id.desc()).limit(100))
    return jsonify([event.to_dict() for event in events.scalars()]), 200
