import enum
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Enum, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from .database import Base

def new_id():
    return str(uuid4())

def now():
    return datetime.now(timezone.utc)

class Role(str, enum.Enum):
    admin = "admin"
    student = "student"
    business = "business"

class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=new_id)
    email = Column(String(254), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    password_hash = Column(Text, nullable=False)
    role = Column(Enum(Role, name="user_role"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)

class LoginSession(Base):
    __tablename__ = "login_sessions"
    token_hash = Column(String(64), primary_key=True)
    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)

class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (CheckConstraint("score >= 0 AND score <= 100"),)
    id = Column(String(36), primary_key=True, default=new_id)
    owner_id = Column(ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(300), nullable=False)
    company = Column(String(200), nullable=False)
    industry = Column(String(100), nullable=False)
    level = Column(String(30), nullable=False, default="Черновик")
    score = Column(Integer, nullable=False, default=0)
    summary = Column(Text, nullable=False)
    users = Column(Text, nullable=False)
    data = Column(Text, nullable=False)
    deadline = Column(String(200), nullable=False)
    tags = Column(JSONB, nullable=False, default=list)
    missing = Column(JSONB, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)

class Proposal(Base):
    __tablename__ = "proposals"
    id = Column(String(36), primary_key=True, default=new_id)
    task_id = Column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(ForeignKey("users.id"), nullable=False, index=True)
    team_name = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)
