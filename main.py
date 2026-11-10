"""Pingboard FastAPI entrypoint and team presence API."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Literal

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sse_starlette.sse import EventSourceResponse

from events import bus
from models import Base, Member

engine = create_async_engine("sqlite+aiosqlite:///./pingboard.db")
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

AllowedStatus = Literal["available", "busy", "away", "meeting", "offline"]


async def init_db() -> None:
    """Create database tables if missing."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


async def get_db():
    """Yield an async database session."""
    async with async_session() as session:
        yield session


class MemberCreate(BaseModel):
    """Member registration payload."""

    name: str = Field(..., min_length=1, max_length=100)
    avatar: str = Field(default="", max_length=16)

    @field_validator("name")
    @classmethod
    def strip_non_empty(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Member name must not be blank.")
        return cleaned


class StatusUpdate(BaseModel):
    """Member status update payload."""

    status: AllowedStatus
    message: str | None = Field(default="", max_length=200)


def _member_dict(m: Member) -> dict[str, Any]:
    return {
        "id": m.id,
        "name": m.name,
        "avatar": m.avatar,
        "status": m.status,
        "message": m.message,
        "updated_at": m.updated_at.isoformat() if m.updated_at else None,
    }


def create_app() -> FastAPI:
    """Construct the FastAPI Pingboard application."""
    application = FastAPI(title="pingboard", version="1.0.0", lifespan=lifespan)
    application.mount("/static", StaticFiles(directory="static"), name="static")

    @application.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "healthy"}

    @application.get("/")
    async def index() -> FileResponse:
        return FileResponse("static/index.html")

    @application.post("/api/members", status_code=201)
    async def create_member(
        data: MemberCreate, db: AsyncSession = Depends(get_db)
    ) -> dict[str, Any]:
        existing = await db.scalar(
            select(Member).where(func.lower(Member.name) == data.name.lower())
        )
        if existing:
            raise HTTPException(status_code=409, detail="Member already exists.")

        member = Member(name=data.name, avatar=data.avatar or "\U0001f464")
        db.add(member)
        try:
            await db.commit()
        except IntegrityError as exc:
            await db.rollback()
            raise HTTPException(status_code=409, detail="Member already exists.") from exc
        await db.refresh(member)
        payload = _member_dict(member)
        await bus.publish("member_joined", payload)
        return payload

    @application.get("/api/members")
    async def list_members(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
        result = await db.execute(select(Member).order_by(Member.name))
        return [_member_dict(m) for m in result.scalars().all()]

    @application.put("/api/members/{member_id}/status")
    async def update_status(
        member_id: int,
        data: StatusUpdate,
        db: AsyncSession = Depends(get_db),
    ) -> dict[str, Any]:
        member = await db.scalar(select(Member).where(Member.id == member_id))
        if not member:
            raise HTTPException(status_code=404, detail="Member not found.")

        member.status = data.status
        member.message = (data.message or "").strip()
        await db.commit()
        await db.refresh(member)
        payload = _member_dict(member)
        await bus.publish("status_changed", payload)
        return payload

    @application.delete("/api/members/{member_id}")
    async def remove_member(
        member_id: int, db: AsyncSession = Depends(get_db)
    ) -> dict[str, bool]:
        member = await db.scalar(select(Member).where(Member.id == member_id))
        if not member:
            raise HTTPException(status_code=404, detail="Member not found.")
        await db.delete(member)
        await db.commit()
        await bus.publish("member_left", {"id": member_id})
        return {"ok": True}

    @application.get("/api/events")
    async def sse_events() -> EventSourceResponse:
        queue = bus.subscribe()
        return EventSourceResponse(bus.stream(queue))

    return application


app = create_app()
