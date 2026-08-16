# pingboard

Minimalist team presence and status board with real-time updates via Server-Sent Events (SSE).

## Features

- Real-time status synchronization across all connected clients via SSE
- Quick status switching (Available, Busy, Away, Meeting, Offline)
- Custom status message & emoji avatar picker
- Lightweight SQLite persistence with async SQLAlchemy 2.0
- Clean zero-dependency frontend

## Quick Start

### Docker

```bash
docker compose up --build
```

### Local Development

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Navigate to `http://localhost:8000` in your browser.

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/members` | Get all board members and statuses |
| POST | `/api/members` | Join board with name and emoji avatar |
| PUT | `/api/members/:id/status` | Update status & status message |
| DELETE | `/api/members/:id` | Remove member from board |
| GET | `/api/events` | SSE stream for real-time board updates |

## Stack

- **Backend:** FastAPI, SQLAlchemy 2.0 (async), SQLite (`aiosqlite`), `sse-starlette`
- **Frontend:** Vanilla JS / modern CSS
- **Container:** Docker & Docker Compose
