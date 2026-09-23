from datetime import datetime
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints
from .models import Role

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
LongText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=10000)]

class Register(BaseModel):
    email: EmailStr
    name: ShortText
    password: str = Field(min_length=10, max_length=128)
    role: Literal["student", "business"] = "student"

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    name: str
    role: Role

class RoleUpdate(BaseModel):
    role: Role

class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]
    company: ShortText
    industry: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    summary: LongText
    users: LongText
    data: LongText
    deadline: ShortText
    tags: list[ShortText] = Field(default_factory=list, max_length=20)

class TaskOut(TaskCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    owner_id: str
    level: str
    score: int
    missing: list[str]
    proposals: int = 0
    created_at: datetime

class ProposalCreate(BaseModel):
    team_name: ShortText
    message: LongText

class ProposalOut(ProposalCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    task_id: str
    student_id: str
    created_at: datetime
