from flask import Blueprint, Response, jsonify

from app.schemas import (
    BlockCreateSchema,
    BlockUpdateSchema,
    BookingCreateSchema,
    BookingUpdateSchema,
    PropertyCreateSchema,
    UserCreateSchema,
    UserUpdateSchema,
)

docs_bp = Blueprint("api_docs", __name__)


def reference(name: str) -> dict:
    return {"$ref": f"#/components/schemas/{name}"}


def operation(
    summary: str,
    tag: str,
    status: str = "200",
    response_schema: dict | None = None,
    request_schema: str | None = None,
    query: list[dict] | None = None,
) -> dict:
    result = {
        "summary": summary,
        "tags": [tag],
        "responses": {
            status: (
                {"description": "Success"}
                if response_schema is None
                else {
                    "description": "Success",
                    "content": {"application/json": {"schema": response_schema}},
                }
            ),
            "400": {"$ref": "#/components/responses/BadRequest"},
            "401": {"$ref": "#/components/responses/Unauthorized"},
            "403": {"$ref": "#/components/responses/Forbidden"},
            "404": {"$ref": "#/components/responses/NotFound"},
            "409": {"$ref": "#/components/responses/Conflict"},
        },
        "parameters": [
            {
                "in": "header",
                "name": "X-Role",
                "required": False,
                "description": "Demo mode only. Ignored when API_KEY_REQUIRED=true.",
                "schema": {"type": "string", "enum": ["ADMIN", "MANAGER", "GUEST"]},
            }
        ],
    }
    if request_schema:
        result["requestBody"] = {
            "required": True,
            "content": {"application/json": {"schema": reference(request_schema)}},
        }
    if query:
        result["parameters"].extend(query)
    return result


def path_id(name: str) -> dict:
    return {
        "in": "path",
        "name": name,
        "required": True,
        "schema": {"type": "integer", "minimum": 1},
    }


def list_of(name: str) -> dict:
    return {"type": "array", "items": reference(name)}


def error_response(description: str) -> dict:
    return {
        "description": description,
        "content": {"application/json": {"schema": reference("Error")}},
    }


@docs_bp.get("/openapi.json")
def openapi_spec():
    property_filter = {
        "in": "query", "name": "property_id", "required": False,
        "schema": {"type": "integer", "minimum": 1},
    }
    status_filter = {
        "in": "query", "name": "status", "required": False,
        "schema": {"type": "string", "enum": ["CONFIRMED", "CANCELED"]},
    }
    paths = {
        "/api/v1/properties": {
            "get": operation("List properties", "Properties", response_schema=list_of("Property")),
            "post": operation(
                "Create property", "Properties", "201", reference("Property"), "PropertyCreateSchema"
            ),
        },
        "/api/v1/properties/{property_id}": {
            "parameters": [path_id("property_id")],
            "get": operation("Get property", "Properties", response_schema=reference("Property")),
        },
        "/api/v1/bookings": {
            "get": operation(
                "List bookings", "Bookings", response_schema=list_of("Booking"),
                query=[property_filter, status_filter],
            ),
            "post": operation(
                "Create booking", "Bookings", "201", reference("Booking"), "BookingCreateSchema"
            ),
        },
        "/api/v1/bookings/{booking_id}": {
            "parameters": [path_id("booking_id")],
            "get": operation("Get booking", "Bookings", response_schema=reference("Booking")),
            "put": operation(
                "Update booking", "Bookings", response_schema=reference("Booking"),
                request_schema="BookingUpdateSchema",
            ),
            "patch": operation(
                "Partially update booking", "Bookings", response_schema=reference("Booking"),
                request_schema="BookingUpdateSchema",
            ),
            "delete": operation("Delete booking", "Bookings", "204"),
        },
        "/api/v1/bookings/{booking_id}/cancel": {
            "parameters": [path_id("booking_id")],
            "post": operation("Cancel booking", "Bookings", response_schema=reference("Booking")),
        },
        "/api/v1/bookings/{booking_id}/rebook": {
            "parameters": [path_id("booking_id")],
            "post": operation("Rebook canceled booking", "Bookings", response_schema=reference("Booking")),
        },
        "/api/v1/blocks": {
            "get": operation(
                "List blocks", "Blocks", response_schema=list_of("Block"), query=[property_filter]
            ),
            "post": operation("Create block", "Blocks", "201", reference("Block"), "BlockCreateSchema"),
        },
        "/api/v1/blocks/{block_id}": {
            "parameters": [path_id("block_id")],
            "get": operation("Get block", "Blocks", response_schema=reference("Block")),
            "put": operation(
                "Update block", "Blocks", response_schema=reference("Block"),
                request_schema="BlockUpdateSchema",
            ),
            "patch": operation(
                "Partially update block", "Blocks", response_schema=reference("Block"),
                request_schema="BlockUpdateSchema",
            ),
            "delete": operation("Delete block", "Blocks", "204"),
        },
        "/api/v1/admin/users": {
            "get": operation("List users (ADMIN)", "Admin", response_schema=list_of("User")),
            "post": operation(
                "Create user and one-time API key (ADMIN)", "Admin", "201",
                reference("UserWithKey"), "UserCreateSchema",
            ),
        },
        "/api/v1/admin/users/{user_id}": {
            "parameters": [path_id("user_id")],
            "patch": operation(
                "Update user role or name (ADMIN)", "Admin",
                response_schema=reference("User"), request_schema="UserUpdateSchema",
            ),
            "delete": operation("Revoke user key (ADMIN)", "Admin", "204"),
        },
        "/api/v1/admin/audit": {
            "get": operation("Recent successful writes (ADMIN)", "Admin",
                             response_schema=list_of("AuditEvent")),
        },
    }
    schemas = {
        "Property": {
            "type": "object", "required": ["id", "name", "country_code"],
            "properties": {
                "id": {"type": "integer"}, "name": {"type": "string"},
                "country_code": {"type": "string"},
            },
        },
        "Booking": {
            "type": "object",
            "required": ["id", "property_id", "guest_name", "start_date", "end_date", "status"],
            "properties": {
                "id": {"type": "integer"}, "property_id": {"type": "integer"},
                "guest_name": {"type": "string"},
                "start_date": {"type": "string", "format": "date"},
                "end_date": {"type": "string", "format": "date"},
                "status": {"type": "string", "enum": ["CONFIRMED", "CANCELED"]},
            },
        },
        "Block": {
            "type": "object", "required": ["id", "property_id", "start_date", "end_date"],
            "properties": {
                "id": {"type": "integer"}, "property_id": {"type": "integer"},
                "start_date": {"type": "string", "format": "date"},
                "end_date": {"type": "string", "format": "date"},
            },
        },
        "User": {
            "type": "object", "required": ["id", "name", "role"],
            "properties": {
                "id": {"type": "integer"}, "name": {"type": "string"},
                "role": {"type": "string", "enum": ["ADMIN", "MANAGER", "GUEST"]},
            },
        },
        "UserWithKey": {
            "allOf": [
                reference("User"),
                {"type": "object", "required": ["api_key"],
                 "properties": {"api_key": {"type": "string"}}},
            ]
        },
        "AuditEvent": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"}, "role": {"type": "string"},
                "method": {"type": "string"}, "path": {"type": "string"},
                "status_code": {"type": "integer"},
                "created_at": {"type": "string", "format": "date-time"},
            },
        },
        "Error": {
            "type": "object", "required": ["error", "details"],
            "properties": {"error": {"type": "string"}, "details": {"type": "string"}},
        },
    }
    for schema_type in (
        PropertyCreateSchema, BookingCreateSchema, BookingUpdateSchema,
        BlockCreateSchema, BlockUpdateSchema, UserCreateSchema, UserUpdateSchema,
    ):
        schemas[schema_type.__name__] = schema_type.model_json_schema()
    return jsonify({
        "openapi": "3.1.0",
        "info": {
            "title": "Hostfully Booking API",
            "version": "1.0.0",
            "description": "Inclusive booking and block availability API. Overlaps return 409.",
        },
        "servers": [{"url": "/"}],
        "security": [{"ApiKeyAuth": []}, {}],
        "paths": paths,
        "components": {
            "schemas": schemas,
            "securitySchemes": {
                "ApiKeyAuth": {"type": "apiKey", "in": "header", "name": "X-API-Key"}
            },
            "responses": {
                "BadRequest": error_response("Invalid request"),
                "Unauthorized": error_response("Missing or invalid API key"),
                "Forbidden": error_response("Role does not allow this action"),
                "NotFound": error_response("Resource not found"),
                "Conflict": error_response("Availability or state conflict"),
            },
        },
    })


@docs_bp.get("/docs")
def swagger_ui():
    return Response(
        """<!doctype html><html lang="en"><head><meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Hostfully API docs</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
        </head><body><div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
        <script>SwaggerUIBundle({url:"/openapi.json",dom_id:"#swagger-ui"});</script>
        </body></html>""",
        mimetype="text/html",
    )
