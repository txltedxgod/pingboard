import asyncio
import json
from typing import AsyncGenerator


class EventBus:
    """Simple pub/sub for SSE broadcasting."""

    def __init__(self):
        self._subscribers: list[asyncio.Queue] = []

    def subscribe(self) -> asyncio.Queue:
        q = asyncio.Queue(maxsize=50)
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        self._subscribers.remove(q)

    async def publish(self, event_type: str, data: dict):
        msg = json.dumps({'type': event_type, 'data': data})
        dead = []
        for q in self._subscribers:
            try:
                q.put_nowait(msg)
            except asyncio.QueueFull:
                dead.append(q)
        for q in dead:
            self._subscribers.remove(q)

    async def stream(self, q: asyncio.Queue) -> AsyncGenerator[str, None]:
        try:
            while True:
                msg = await q.get()
                yield msg
        except asyncio.CancelledError:
            pass


bus = EventBus()
