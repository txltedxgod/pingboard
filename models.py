from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime


class Base(DeclarativeBase):
    pass


class Member(Base):
    __tablename__ = 'members'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    avatar = Column(String(10), default='')  # emoji avatar
    status = Column(String(20), default='available')  # available, busy, away, meeting, offline
    message = Column(String(200), default='')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
