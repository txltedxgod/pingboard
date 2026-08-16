from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from sse_starlette.sse import EventSourceResponse
from models import Base, Member
from events import bus
from pydantic import BaseModel
from typing import Optional
from contextlib import asynccontextmanager

engine = create_async_engine('sqlite+aiosqlite:///./pingboard.db')
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title='pingboard', lifespan=lifespan)
app.mount('/static', StaticFiles(directory='static'), name='static')


async def get_db():
    async with async_session() as session:
        yield session


class MemberCreate(BaseModel):
    name: str
    avatar: str = ''


class StatusUpdate(BaseModel):
    status: str  # available, busy, away, meeting, offline
    message: Optional[str] = ''


@app.get('/')
async def index():
    return FileResponse('static/index.html')


@app.post('/api/members')
async def create_member(data: MemberCreate, db: AsyncSession = Depends(get_db)):
    member = Member(name=data.name, avatar=data.avatar or '\U0001f464')
    db.add(member)
    await db.commit()
    await db.refresh(member)
    await bus.publish('member_joined', _member_dict(member))
    return _member_dict(member)


@app.get('/api/members')
async def list_members(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Member).order_by(Member.name))
    members = result.scalars().all()
    return [_member_dict(m) for m in members]


@app.put('/api/members/{member_id}/status')
async def update_status(
    member_id: int,
    data: StatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Member).where(Member.id == member_id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(404)

    member.status = data.status
    member.message = data.message or ''
    await db.commit()
    await db.refresh(member)
    await bus.publish('status_changed', _member_dict(member))
    return _member_dict(member)


@app.delete('/api/members/{member_id}')
async def remove_member(member_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Member).where(Member.id == member_id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(404)
    await db.delete(member)
    await db.commit()
    await bus.publish('member_left', {'id': member_id})
    return {'ok': True}


@app.get('/api/events')
async def sse_events():
    queue = bus.subscribe()
    return EventSourceResponse(bus.stream(queue))


def _member_dict(m: Member):
    return {
        'id': m.id,
        'name': m.name,
        'avatar': m.avatar,
        'status': m.status,
        'message': m.message,
        'updated_at': m.updated_at.isoformat() if m.updated_at else None
    }
