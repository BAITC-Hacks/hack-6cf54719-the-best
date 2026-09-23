<<<<<<< HEAD
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
=======
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(512))
    role: Mapped[str] = mapped_column(String(20), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    company_profile: Mapped["CompanyProfile | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )


class CompanyProfile(Base):
    __tablename__ = "company_profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    company_name: Mapped[str] = mapped_column(String(160))
    user: Mapped[User] = relationship(back_populates="company_profile")


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    invite_code: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    members: Mapped[list["TeamMember"]] = relationship(cascade="all, delete-orphan")


class TeamMember(Base):
    __tablename__ = "team_members"
    __table_args__ = (UniqueConstraint("team_id", "user_id", name="uq_team_member"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    user: Mapped[User] = relationship()


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(180))
    description: Mapped[str] = mapped_column(Text, default="")
    industry: Mapped[str] = mapped_column(String(100), default="")
    target_users: Mapped[str] = mapped_column(Text, default="")
    available_data: Mapped[str] = mapped_column(Text, default="")
    success_criteria: Mapped[str] = mapped_column(Text, default="")
    deadline: Mapped[str] = mapped_column(String(120), default="")
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    source_company: Mapped[str | None] = mapped_column(String(180), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    owner: Mapped[User] = relationship()
    applications: Mapped[list["Application"]] = relationship(back_populates="task", cascade="all, delete-orphan")


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("task_id", "team_id", name="uq_task_team_application"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), index=True)
    submitted_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    pitch: Mapped[str] = mapped_column(Text)
    prototype_url: Mapped[str] = mapped_column(String(1000), default="")
    status: Mapped[str] = mapped_column(String(20), default="submitted", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    team: Mapped[Team] = relationship()
    task: Mapped[Task] = relationship(back_populates="applications")
    submitter: Mapped[User] = relationship()
>>>>>>> feature/Branch-raiymbek
