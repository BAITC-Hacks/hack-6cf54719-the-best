"""API каталога задач.

Запуск из корня проекта: uvicorn backend.main:app --reload
Зависимости: fastapi, uvicorn.
"""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field


# Создание приложения. Интерактивная документация доступна по /docs.
app = FastAPI(title="AI Sana — каталог задач", version="0.1.0")

# CORS понадобится для запросов из браузера с другого origin.
# Streamlit выполняет серверные HTTP-запросы, для них CORS не требуется.


# Модели запросов и ответов.
class Task(BaseModel):
    id: str
    title: str
    company: str
    industry: str
    level: str
    score: int = Field(ge=0, le=100)
    summary: str
    users: str
    data: str
    deadline: str
    tags: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    proposals: int = Field(default=0, ge=0)


class ProposalCreate(BaseModel):
    team_name: str = Field(min_length=1, max_length=200, pattern=r"\S")
    message: str = Field(min_length=1, max_length=10000, pattern=r"\S")


class Proposal(ProposalCreate):
    id: str
    task_id: str
    created_at: datetime


# Временное хранилище: очищается при перезапуске, не общее для процессов.
# Пока пустое. Задачи из frontend/app.py сюда ещё не перенесены.
tasks: dict[str, Task] = {}
proposals: dict[str, list[Proposal]] = {}

# agent.py пока пуст; интеграцию агента можно добавить после его реализации.


def get_task_or_404(task_id: str) -> Task:
    task = tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return task


# API-маршруты.
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/tasks", response_model=list[Task])
def list_tasks() -> list[Task]:
    return list(tasks.values())


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: str) -> Task:
    return get_task_or_404(task_id)


@app.post(
    "/tasks/{task_id}/proposals",
    response_model=Proposal,
    status_code=status.HTTP_201_CREATED,
)
def create_proposal(task_id: str, payload: ProposalCreate) -> Proposal:
    task = get_task_or_404(task_id)
    proposal = Proposal(
        id=str(uuid4()),
        task_id=task_id,
        team_name=payload.team_name,
        message=payload.message,
        created_at=datetime.now(timezone.utc),
    )
    proposals.setdefault(task_id, []).append(proposal)
    task.proposals += 1
    return proposal
