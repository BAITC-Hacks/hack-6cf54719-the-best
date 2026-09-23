from datetime import datetime
<<<<<<< HEAD
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
=======
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, field_validator


Role = Literal["company", "student"]


class RegisterInput(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Role
    company_name: str | None = Field(default=None, max_length=160)
    team_name: str | None = Field(default=None, max_length=120)


class LoginInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    name: str
    role: Role
    company_name: str | None = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class TaskInput(BaseModel):
    title: str = Field(min_length=3, max_length=180)
    description: str = Field(default="", max_length=10000)
    industry: str = Field(default="", max_length=100)
    target_users: str = Field(default="", max_length=3000)
    available_data: str = Field(default="", max_length=3000)
    success_criteria: str = Field(default="", max_length=3000)
    deadline: str = Field(default="", max_length=120)
    tags: list[str] = Field(default_factory=list, max_length=12)

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, tags: list[str]) -> list[str]:
        return list(dict.fromkeys(tag.strip()[:40] for tag in tags if tag.strip()))


class ReadinessFieldOut(BaseModel):
    key: str
    label: str
    weight: int
    points: int
    present: bool
    guidance: str


class TaskOut(BaseModel):
    id: int
    owner_id: int
    company_name: str
    source_url: str | None = None
    is_imported: bool = False
    title: str
    description: str
    industry: str
    target_users: str
    available_data: str
    success_criteria: str
    deadline: str
    tags: list[str]
    status: str
    readiness_score: int
    readiness_label: str
    missing_fields: list[str]
    readiness_breakdown: list[ReadinessFieldOut]
    applications_count: int
    created_at: datetime
    updated_at: datetime


class TeamCreateInput(BaseModel):
    name: str = Field(min_length=2, max_length=120)


class TeamJoinInput(BaseModel):
    invite_code: str = Field(min_length=4, max_length=24)


class TeamMemberOut(BaseModel):
    user_id: int
    name: str
    email: EmailStr


class TeamOut(BaseModel):
    id: int
    name: str
    invite_code: str
    is_owner: bool
    members: list[TeamMemberOut]


class ApplicationCreateInput(BaseModel):
    team_id: int
    pitch: str = Field(min_length=20, max_length=5000)
    prototype_url: HttpUrl | None = None


class ApplicationOut(BaseModel):
    id: int
    task_id: int
    task_title: str
    team_id: int
    team_name: str
    submitted_by_name: str
    pitch: str
    prototype_url: str
    status: str
    created_at: datetime
    company_name: str | None = None


class TaskAssistInput(BaseModel):
    title: str = ""
    description: str = ""
    industry: str = ""
    target_users: str = ""
    available_data: str = ""
    success_criteria: str = ""
    deadline: str = ""


class TaskAssistOutput(BaseModel):
    suggestions: dict[str, str]
    note: str
>>>>>>> feature/Branch-raiymbek
