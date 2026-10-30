import hashlib
import secrets
from functools import wraps

from flask import current_app, g, request
from sqlalchemy import select

from app.errors import ForbiddenError, UnauthorizedError
from app.extensions import db
from app.models import User


def current_role() -> str:
    if current_app.config.get("API_KEY_REQUIRED"):
        provided_key = request.headers.get("X-API-Key", "")
        if not provided_key:
            raise UnauthorizedError("Missing X-API-Key header.")
        master_key = current_app.config["API_SECRET_KEY"]
        if secrets.compare_digest(provided_key, master_key):
            return "ADMIN"
        key_hash = hashlib.sha256(provided_key.encode()).hexdigest()
        user = db.session.execute(select(User).where(User.api_key_hash == key_hash)).scalar_one_or_none()
        if user is None:
            raise UnauthorizedError("Invalid X-API-Key header.")
        return user.role
    return request.headers.get("X-Role", "ADMIN").upper()


def require_role(*allowed_roles: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            role = current_role()
            g.current_role = role
            if allowed_roles and role not in allowed_roles:
                raise ForbiddenError(
                    f"Role '{role}' is not permitted to perform this action. Allowed: {', '.join(allowed_roles)}."
                )
            return fn(*args, **kwargs)
        return wrapper
    return decorator
