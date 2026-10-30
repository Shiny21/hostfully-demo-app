# CLAUDE.md — Master Technical Specification & Implementation Guide

## 1. Project Overview
Build a RESTful web service in **Python 3.10+** using **Flask 3.x**, **SQLAlchemy 2.0**, and **Pydantic v2** that manages **Properties**, **Bookings**, and **Blocks**, enforces strict inclusive date-overlap validation, and returns structured JSON errors. PostgreSQL uses a parent-property row lock for concurrent availability writes. Vercel deployment requires a persistent PostgreSQL URL. `/admin` is an interactive API playground and `/docs` serves Swagger UI.

## 2. Core Entities & Schema Rules
1. **Property (`properties`)**:
   - `id`: Integer PK
   - `name`: String(120), non-null
   - `country_code`: String(2), uppercase ISO-3166 alpha-2 (e.g., `US`, `PT`)
2. **Booking (`bookings`)**:
   - `id`: Integer PK
   - `property_id`: Integer FK -> `properties.id` (indexed)
   - `guest_name`: String(120), non-null
   - `start_date`: Date, non-null
   - `end_date`: Date, non-null
   - `status`: Enum (`CONFIRMED`, `CANCELED`), default `CONFIRMED`
   - Composite index: `(property_id, status, start_date, end_date)`
3. **Block (`blocks`)**:
   - `id`: Integer PK
   - `property_id`: Integer FK -> `properties.id` (indexed)
   - `start_date`: Date, non-null
   - `end_date`: Date, non-null
   - Composite index: `(property_id, start_date, end_date)`

## 3. Inclusive Overlap Formula (Critical Requirement)
Overlap is **inclusive of boundaries** (`E` and `N` sharing even 1 day is a conflict):
```python
existing.start_date <= new_end_date and existing.end_date >= new_start_date
```
Verify all boundary cases in `tests/test_overlap_unit.py`:
1. strictly before -> No overlap
2. strictly after -> No overlap
3. fully inside -> Overlap (Yes)
4. touches only start boundary -> Overlap (Yes)
5. touches only end boundary -> Overlap (Yes)
6. fully contains existing -> Overlap (Yes)

## 4. Error Handling Contract
Every error response MUST return:
```json
{
  "error": "Human-readable error category",
  "details": "Specific explanation or list of field errors"
}
```
- `400 Bad Request`: Missing required fields, invalid JSON, malformed dates, or `start_date >= end_date`.
- `401 Unauthorized` / `403 Forbidden`: Invalid API key or insufficient role permissions when auth is enabled.
- `404 Not Found`: Non-existent `property_id`, `booking_id`, or `block_id`.
- `409 Conflict`: Date overlap with an existing `CONFIRMED` booking or block, or invalid state transition.
- `500 Internal Server Error`: Generic catch-all handler.

## 5. Required REST Endpoints
- `POST /api/v1/properties`, `GET /api/v1/properties/<id>`, `GET /api/v1/properties`
- `POST /api/v1/bookings`, `GET /api/v1/bookings/<id>`, `GET /api/v1/bookings`, `PUT|PATCH /api/v1/bookings/<id>`, `POST /api/v1/bookings/<id>/cancel`, `POST /api/v1/bookings/<id>/rebook`, `DELETE /api/v1/bookings/<id>`
- `POST /api/v1/blocks`, `GET /api/v1/blocks`, `GET /api/v1/blocks/<id>`, `PUT|PATCH /api/v1/blocks/<id>`, `DELETE /api/v1/blocks/<id>`
