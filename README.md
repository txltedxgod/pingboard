# pingboard

> Minimalist team presence and status board with real-time updates via Server-Sent Events (SSE).

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![SSE](https://img.shields.io/badge/SSE-Realtime-06B6D4?style=flat-square)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

`#status-board` `#presence` `#team-collaboration` `#sse` `#fastapi` `#vanilla-js` `#remote-work`

---

## Features

- **Real-Time Presence:** Live status updates across all team members powered by Server-Sent Events (SSE).
- **Quick Status Switching:** Instant toggle between Available, Busy, Away, Meeting, and Offline.
- **Custom Status & Avatars:** Emoji avatar picker and customizable status text.
- **Zero-Dependency Frontend:** Lightweight, blazing fast modern CSS & Vanilla JS.
- **Lightweight Backend:** Async SQLite with SQLAlchemy 2.0.

## Quick Start

### With Docker

```bash
docker compose up --build
```

### Local Development

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Open `http://localhost:8000` in your browser.

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/members` | Get all board members and current statuses |
| `POST` | `/api/members` | Join the status board |
| `PUT` | `/api/members/:id/status` | Update member status & status note |
| `DELETE` | `/api/members/:id` | Leave or remove member from board |
| `GET` | `/api/events` | SSE event stream for live synchronization |
