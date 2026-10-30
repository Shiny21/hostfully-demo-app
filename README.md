# Hostfully Property Booking API

A Flask REST API for properties, guest bookings, and owner blocks. Dates are inclusive: a booking that shares its start or end day with a confirmed booking or block on the same property is rejected.

Open [the admin playground](http://localhost:5000/admin) to manage sample records and see API responses. [Swagger UI](http://localhost:5000/docs) documents the endpoints, and [OpenAPI JSON](http://localhost:5000/openapi.json) is available for tools.

## Run on Windows with Docker

```powershell
docker compose up --build -d
Invoke-RestMethod http://localhost:5000/health
docker compose run --rm api pytest
docker compose run --rm api ruff check app tests
docker compose down
```

The API listens on `http://localhost:5000`. PostgreSQL runs in the Compose stack. `docker compose down` removes its container and data; this setup is for local development and review.

The test suite uses SQLite in memory, so it does not need the PostgreSQL container. After building the image, `docker run --rm -v "${PWD}:/srv/app" -w /srv/app hostfully-booking-api-api pytest` runs it without Compose.

## API

All paths start with `/api/v1`. Send JSON for create and update requests.

| Resource | Methods and paths |
| --- | --- |
| Properties | `POST /properties`, `GET /properties`, `GET /properties/<id>` |
| Bookings | `POST /bookings`, `GET /bookings`, `GET /bookings/<id>`, `PUT` or `PATCH /bookings/<id>`, `POST /bookings/<id>/cancel`, `POST /bookings/<id>/rebook`, `DELETE /bookings/<id>` |
| Blocks | `POST /blocks`, `GET /blocks`, `GET /blocks/<id>`, `PUT` or `PATCH /blocks/<id>`, `DELETE /blocks/<id>` |
| Admin | `GET` or `POST /admin/users`, `PATCH` or `DELETE /admin/users/<id>`, `GET /admin/audit` |

Booking lists accept `property_id` and `status` filters; block lists accept `property_id`. A successful create returns `201`, delete returns `204`, and reads or updates return `200`.

Example PowerShell request after starting Compose:

```powershell
$property = Invoke-RestMethod http://localhost:5000/api/v1/properties -Method Post -ContentType application/json -Body '{"name":"Coastal Villa","country_code":"PT"}'
$booking = @{property_id=$property.id;guest_name='Alex';start_date='2026-11-11';end_date='2026-11-16'} | ConvertTo-Json
Invoke-RestMethod http://localhost:5000/api/v1/bookings -Method Post -ContentType application/json -Body $booking
```

Requests with missing or malformed fields, or `start_date >= end_date`, return `400`. Unknown resource IDs return `404`. Overlaps and invalid rebook transitions return `409`. Errors have the form `{"error":"Conflict","details":"..."}`; unexpected errors return a generic `500` body.

## Vercel deployment

The Vercel entrypoint is [`api/index.py`](api/index.py), with routing in [`vercel.json`](vercel.json). Connect this repository to a Vercel project and set **`DATABASE_URL` or `POSTGRES_URL`** to a persistent PostgreSQL database in the Vercel project settings before deployment. `postgres://`, `postgresql://`, and `postgresql+psycopg2://` URLs are accepted. Include the provider's required SSL parameters in the URL. The app creates its tables on startup.

Vercel runs short-lived functions and cannot host the PostgreSQL Docker container from `docker-compose.yml`. A local Docker database is also not reachable from a public deployment. The simplest setup with this code is a hosted PostgreSQL database, such as Neon: create a database there, copy its PostgreSQL connection string, and add it as `DATABASE_URL` in Vercel's project environment variables. Keep that string out of GitHub. You may set `AUTO_SEED_DEMO=true` for one example property, booking, and block. Import the GitHub repository into Vercel as a Python project, deploy, then check `/health`, `/admin`, and `/docs`.

The default SQLite in-memory database is intended for local tests. On Vercel, startup fails clearly if no PostgreSQL URL is configured, because separate function instances would otherwise lose or disagree on bookings. In the default open demo mode, anyone with the public URL can change demo data; use only disposable sample records. For enforced roles, set `API_KEY_REQUIRED=true` and a private `API_SECRET_KEY`. `/docs` loads Swagger UI assets from a public CDN.

## Admin playground and roles

The `/admin` screen creates properties, bookings, blocks, and named API users; it lists current records and recent successful write requests. It can update, cancel, rebook, and delete bookings, and update or delete blocks. Its response panel shows status codes and conflict details. No seed data is required: create a property first, then use its ID through the dropdowns.

In the default **open demo mode**, no API key is required. The role selector sends `X-Role` to demonstrate these permissions:

| Role | Allowed actions |
| --- | --- |
| `GUEST` | Read properties and blocks; create, read, update, cancel, and rebook bookings. |
| `MANAGER` | Guest actions, plus create properties, create/update/delete blocks, and hard-delete bookings. |
| `ADMIN` | All actions, including creating users, changing roles, revoking keys, and reading audit events. |

For enforced key-based roles, set `API_KEY_REQUIRED=true` and set `API_SECRET_KEY` to a long random value in the deployment environment. A missing master secret stops startup. Supply the master secret as `X-API-Key` to create users at `POST /api/v1/admin/users`; that response returns each new user's key **once**. Later list responses never include keys. In strict mode, a stored user key determines its role and `X-Role` cannot elevate it. The browser stores the typed key only in the current page; refreshing clears it. This is simple API-key authentication for the demo, with no password login or self-service registration. Successful write requests appear in the admin audit view without request bodies or keys.

## Design notes

Flask keeps the HTTP layer small. Pydantic validates JSON fields and date order. SQLAlchemy persists the three required entities in a real relational database. Tests use SQLite in memory for quick, isolated runs; Docker and the intended Vercel deployment use PostgreSQL.

An inclusive overlap exists when `existing.start_date <= new_end_date` **and** `existing.end_date >= new_start_date`. The availability query checks confirmed bookings and blocks for the same property. It runs for booking creation and date updates, rebooking, and block creation and updates. Canceled bookings do not reserve dates. Updating an existing booking or block excludes its own ID from the check. A valid request prevented by another reservation returns `409 Conflict`, because the conflict depends on current database state.

On PostgreSQL, booking and block writes lock the parent property row before checking availability, serializing competing requests for one property. SQLite does not provide equivalent row locks, so the in-memory test setup does not prove concurrent-write safety. The public API defaults to open demo mode to make the technical test easy to exercise; use strict key mode when exposing role-restricted operations. The audit view keeps the latest 100 successful writes and is not a full security audit trail. Automated coverage is reported but is not required to reach a fixed percentage.

## Technical-test checklist

- Python 3.10+ and Flask REST service: implemented.
- Property, Booking, and Block entities and all requested create/read/list/update/cancel/rebook/delete operations: implemented and API tested.
- Inclusive overlap on booking create, update, and rebook, scoped to one property and excluding canceled bookings: implemented and tested, including both touching boundaries. Block writes use the same check.
- Required-field and date validation, structured `400`/`404`/`409` errors, and generic `500` handling: implemented; representative API error paths tested.
- Real ORM-backed persistence: SQLite for isolated tests; PostgreSQL for Docker and a persistent Vercel demo.
- Unit overlap tests, API tests, and the required design notes: included.
- Optional concurrency and simple authentication: PostgreSQL property-row locking and API-key mode included.
- Public GitHub upload and emailing a link are submission steps for the project owner; they are not performed by the app.
