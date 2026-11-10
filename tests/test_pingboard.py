"""Unit and integration tests for Pingboard EventBus and presence API."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import main
from events import EventBus
from models import Base


@pytest.fixture()
def board_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    db_file = tmp_path / "pingboard_test.db"
    test_engine = create_async_engine(f"sqlite+aiosqlite:///{db_file.as_posix()}")
    test_session_maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    monkeypatch.setattr(main, "engine", test_engine)
    monkeypatch.setattr(main, "async_session", test_session_maker)

    async def test_init_db() -> None:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    monkeypatch.setattr(main, "init_db", test_init_db)

    application = main.create_app()
    with TestClient(application) as client:
        yield client


@pytest.mark.asyncio
async def test_event_bus_cleanup_on_disconnect_and_overflow() -> None:
    bus = EventBus(max_queue_size=2)
    q = bus.subscribe()
    assert bus.subscriber_count == 1

    stream = bus.stream(q)
    await bus.publish("ping", {"hello": "world"})
    msg = await asyncio.wait_for(stream.__anext__(), timeout=1.0)
    assert '"ping"' in msg

    # Closing the async generator triggers finally -> unsubscribe (prevents leak)
    await stream.aclose()
    assert bus.subscriber_count == 0

    # Full queue gets pruned automatically on publish
    slow_q = bus.subscribe()
    await bus.publish("e1", {})
    await bus.publish("e2", {})
    await bus.publish("e3", {})
    assert bus.subscriber_count == 0
    bus.unsubscribe(slow_q)


def test_member_lifecycle_duplicate_and_validation(board_client: TestClient) -> None:
    assert board_client.get("/health").json() == {"status": "healthy"}
    assert board_client.get("/").status_code == 200

    res = board_client.post("/api/members", json={"name": "Alice"})
    assert res.status_code == 201
    member_id = res.json()["id"]

    # Case-insensitive duplicate returns 409 Conflict instead of 500
    dup = board_client.post("/api/members", json={"name": "alice"})
    assert dup.status_code == 409

    # Valid status update succeeds; unsupported status returns 422
    upd = board_client.put(
        f"/api/members/{member_id}/status",
        json={"status": "meeting", "message": "Sprint planning"},
    )
    assert upd.status_code == 200
    assert upd.json()["status"] == "meeting"

    bad = board_client.put(
        f"/api/members/{member_id}/status",
        json={"status": "invalid_state"},
    )
    assert bad.status_code == 422

    deleted = board_client.delete(f"/api/members/{member_id}")
    assert deleted.status_code == 200
    assert board_client.get("/api/members").json() == []
