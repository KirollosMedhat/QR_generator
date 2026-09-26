# QR Generator

A FastAPI service that generates QR codes, tracks how many times each one has been scanned, and redirects scanners to the intended destination — backed by PostgreSQL via SQLAlchemy.

## How it works

Each QR code doesn't encode its final destination directly. Instead, it encodes a link back to this service (`/qrcode/{id}/visit`). When scanned:

1. The scanner is redirected to this service.
2. This service increments that QR code's visit count.
3. The scanner is then redirected to the real destination URL, stored in the database.

This design is what makes visit tracking possible at all — a QR code image has no logic of its own, so tracking a "scan" only works if the encoded link passes through a server first.

QR generation itself is never persisted as an image file. Since QR encoding is deterministic (the same input always produces the same code), each QR image is generated on demand from the database record rather than stored on disk — avoiding any dependency on a specific machine's filesystem, which matters for deployment.

## Project structure

| File | Responsibility |
|---|---|
| `database.py` | Engine, session factory, and the shared SQLAlchemy `Base` |
| `tables.py` | The `QRCode` table definition |
| `qr_services.py` | Business logic — creating records, generating QR images, incrementing visits |
| `main.py` | FastAPI app, routes, and request/response handling |

## Data model

Each QR code record stores:

- `id` — auto-incrementing primary key
- `url` — the real destination the scanner is ultimately sent to
- `company` — a plain label for which company/client the QR code belongs to
- `visits` — number of times the QR code has been scanned, incremented atomically on each visit
- `timestamp` — when the record was created

## Setup

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```powershell
uv sync
```

### Environment variables

Create a `.env` file in the project root:

```dotenv
DATABASE_URL=postgresql+psycopg2://postgres:yourpassword@localhost:5432/qr_code_db
BASE_URL=http://127.0.0.1:8000
```

- `DATABASE_URL` — your PostgreSQL connection string
- `BASE_URL` — the public base URL of this service, used to build the link encoded into each QR code

You'll need a PostgreSQL database created ahead of time (e.g. `CREATE DATABASE qr_code_db;`) — tables are created automatically on startup.

### Running

```powershell
uv run uvicorn main:api --reload
```

Interactive API docs are available at `http://127.0.0.1:8000/docs` once running.

## Endpoints

### `POST /create_qrcode`

Creates a new QR code record for a given destination URL and company. If the URL already exists, returns the existing record's ID instead of creating a duplicate.

**Request body:**
```json
{
  "url": "https://example.com",
  "company": "Acme Inc"
}
```

`url` is validated as a well-formed `http`/`https` URL before the request is accepted.

**Response:** the record's `id`.

### `GET /qrcode/{id}`

Returns the QR code as an SVG image for the given record ID — useful for viewing or downloading the code itself. Regenerated on the fly each time, not read from a stored file.

### `GET /qrcode/{id}/visit`

The URL actually encoded inside the QR image. Increments the record's visit count and redirects to the stored destination URL. This is the endpoint a scanner's phone will hit after decoding the QR code.

## Error handling

- Database connectivity issues (e.g. the database becoming unreachable) return a `503` response rather than crashing.
- A duplicate/conflicting write returns a `409` response.
- An invalid `url` in the create request returns a `422` with details on what failed validation.

## Known limitations / not yet built

- No authentication — anyone with network access to this service can create QR codes or view visit counts.
- `company` has no format or length validation.
- Database sessions are managed manually inside each service function rather than via FastAPI's dependency injection (`Depends`) — a planned refactor once shared transactions across multiple operations are needed.
- Currently synchronous (not `async`) — a deliberate choice given expected traffic is low.