from flask import Flask, jsonify
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException


class APIError(Exception):
    status_code = 400
    error_title = "Bad Request"

    def __init__(self, details: str, status_code: int | None = None, error_title: str | None = None):
        super().__init__(details)
        self.details = details
        if status_code is not None:
            self.status_code = status_code
        if error_title is not None:
            self.error_title = error_title


class BadRequestError(APIError):
    status_code = 400
    error_title = "Bad Request"


class NotFoundError(APIError):
    status_code = 404
    error_title = "Not Found"


class ConflictError(APIError):
    status_code = 409
    error_title = "Conflict"


class ForbiddenError(APIError):
    status_code = 403
    error_title = "Forbidden"


class UnauthorizedError(APIError):
    status_code = 401
    error_title = "Unauthorized"


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(APIError)
    def handle_api_error(exc: APIError):
        return jsonify({"error": exc.error_title, "details": exc.details}), exc.status_code

    @app.errorhandler(ValidationError)
    def handle_pydantic_validation_error(exc: ValidationError):
        messages = []
        for err in exc.errors():
            loc = ".".join(str(x) for x in err.get("loc", []))
            msg = err.get("msg", "Invalid value")
            messages.append(f"{loc}: {msg}" if loc else msg)
        return jsonify({"error": "Bad Request", "details": "; ".join(messages)}), 400

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        return jsonify({"error": exc.name, "details": exc.description}), exc.code

    @app.errorhandler(Exception)
    def handle_unexpected_exception(exc: Exception):
        app.logger.exception("Unhandled exception: %s", exc)
        return jsonify({
            "error": "Internal Server Error",
            "details": "An unexpected error occurred on the server."
        }), 500
