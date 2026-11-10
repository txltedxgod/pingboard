"""SSE pub/sub EventBus with safe subscriber cleanup."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator
from typing import Any


class EventBus:
    """In-memory pub/sub for SSE broadcasting."""

    def __init__(self, max_queue_size: int = 50) -> None:
        self._subscribers: list[asyncio.Queue[str]] = []
        self._max_queue_size = max_queue_size

    @property
    def subscriber_count(self) -> int:
        """Number of active subscribed client queues."""
        return len(self._subscribers)

    def subscribe(self) -> asyncio.Queue[str]:
        """Register and return a bounded queue for a new SSE client."""
        q: asyncio.Queue[str] = asyncio.Queue(maxsize=self._max_queue_size)
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[str]) -> None:
        """Safely detach a client queue if still registered."""
        if q in self._subscribers:
            self._subscribers.remove(q)

    async def publish(self, event_type: str, data: dict[str, Any]) -> None:
        """Broadcast an event JSON string to all active queues, dropping full queues."""
        msg = json.dumps({"type": event_type, "data": data})
        dead: list[asyncio.Queue[str]] = []
        for q in self._subscribers:
            try:
                q.put_nowait(msg)
            except asyncio.QueueFull:
                dead.append(q)
        for q in dead:
            self.unsubscribe(q)

    async def stream(self, q: asyncio.Queue[str]) -> AsyncGenerator[str, None]:
        """Yield queued JSON messages and guarantee cleanup on disconnect."""
        try:
            while True:
                yield await q.get()
        finally:
            self.unsubscribe(q)


bus = EventBus()
