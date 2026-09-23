<<<<<<< HEAD
"""Запуск: uvicorn backend.main:app --reload. Документация: /docs."""
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from . import models as m, schemas as s
from .auth import DUMMY_HASH, current_user, oauth2, password_hash, require_roles, token_digest
from .database import get_db

app = FastAPI(title="AI Sana — каталог задач", version="0.2.0")

@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}

@app.post("/auth/register", response_model=s.UserOut, status_code=201)
def register(payload: s.Register, db: Session = Depends(get_db)):
    user = m.User(email=str(payload.email).lower(), name=payload.name,
                  password_hash=password_hash.hash(payload.password), role=m.Role(payload.role))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Email уже зарегистрирован")
    db.refresh(user)
    return user

@app.post("/auth/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(m.User).where(m.User.email == form.username.strip().lower()))
    valid = password_hash.verify(form.password, user.password_hash if user else DUMMY_HASH)
    if not user or not valid:
        raise HTTPException(401, "Неверный email или пароль", headers={"WWW-Authenticate": "Bearer"})
    token = secrets.token_urlsafe(32)
    db.add(m.LoginSession(token_hash=token_digest(token), user_id=user.id,
                         expires_at=datetime.now(timezone.utc) + timedelta(hours=12)))
    db.commit()
    return {"access_token": token, "token_type": "bearer", "expires_in": 43200}

@app.post("/auth/logout", status_code=204)
def logout(token: str = Depends(oauth2), user=Depends(current_user), db: Session = Depends(get_db)):
    db.delete(db.get(m.LoginSession, token_digest(token)))
    db.commit()

@app.get("/auth/me", response_model=s.UserOut)
def me(user=Depends(current_user)):
    return user

@app.get("/admin/users", response_model=list[s.UserOut])
def users(admin=Depends(require_roles(m.Role.admin)), db: Session = Depends(get_db)):
    return db.scalars(select(m.User).order_by(m.User.created_at)).all()

@app.patch("/admin/users/{user_id}/role", response_model=s.UserOut)
def change_role(user_id: str, payload: s.RoleUpdate,
                admin=Depends(require_roles(m.Role.admin)), db: Session = Depends(get_db)):
    user = db.get(m.User, user_id)
    if not user:
        raise HTTPException(404, "Пользователь не найден")
    if user.id == admin.id and payload.role != m.Role.admin:
        raise HTTPException(400, "Нельзя снять роль администратора с себя")
    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user

def task_or_404(db, task_id):
    task = db.get(m.Task, task_id)
    if not task:
        raise HTTPException(404, "Задача не найдена")
    return task

def task_out(task, count=0):
    return s.TaskOut.model_validate(task).model_copy(update={"proposals": count})

@app.get("/tasks", response_model=list[s.TaskOut])
def list_tasks(db: Session = Depends(get_db)):
    counts = select(m.Proposal.task_id, func.count().label("n")).group_by(m.Proposal.task_id).subquery()
    rows = db.execute(select(m.Task, func.coalesce(counts.c.n, 0)).outerjoin(
        counts, m.Task.id == counts.c.task_id).order_by(m.Task.created_at.desc())).all()
    return [task_out(task, count) for task, count in rows]

@app.post("/tasks", response_model=s.TaskOut, status_code=201)
def create_task(payload: s.TaskCreate, user=Depends(require_roles(m.Role.business, m.Role.admin)),
                db: Session = Depends(get_db)):
    task = m.Task(**payload.model_dump(), owner_id=user.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task_out(task)

@app.get("/tasks/{task_id}", response_model=s.TaskOut)
def get_task(task_id: str, db: Session = Depends(get_db)):
    task = task_or_404(db, task_id)
    count = db.scalar(select(func.count()).select_from(m.Proposal).where(m.Proposal.task_id == task_id))
    return task_out(task, count)

@app.post("/tasks/{task_id}/proposals", response_model=s.ProposalOut, status_code=201)
def create_proposal(task_id: str, payload: s.ProposalCreate,
                    user=Depends(require_roles(m.Role.student)), db: Session = Depends(get_db)):
    task_or_404(db, task_id)
    proposal = m.Proposal(**payload.model_dump(), task_id=task_id, student_id=user.id)
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return proposal

@app.get("/tasks/{task_id}/proposals", response_model=list[s.ProposalOut])
def list_proposals(task_id: str, user=Depends(current_user), db: Session = Depends(get_db)):
    task = task_or_404(db, task_id)
    if user.role != m.Role.admin and not (user.role == m.Role.business and task.owner_id == user.id):
        raise HTTPException(403, "Отклики доступны владельцу задачи и администратору")
    return db.scalars(select(m.Proposal).where(m.Proposal.task_id == task_id)).all()
=======
import json
import os
import re
import secrets
from typing import Annotated

import httpx
import jwt
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import String, func, select, text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session, joinedload, selectinload

from database import Base, SessionLocal, engine, get_db
from models import Application, CompanyProfile, Team, TeamMember, Task, User
from schemas import (
    ApplicationCreateInput,
    ApplicationOut,
    LoginInput,
    RegisterInput,
    ReadinessFieldOut,
    TaskAssistInput,
    TaskAssistOutput,
    TaskInput,
    TaskOut,
    TeamCreateInput,
    TeamJoinInput,
    TeamMemberOut,
    TeamOut,
    TokenOut,
    UserOut,
)
from security import create_access_token, hash_password, read_access_token, verify_password


app = FastAPI(
    title="AI Sana API",
    description="Платформа учебных задач от компаний",
    version="1.0.0",
)
bearer_scheme = HTTPBearer(auto_error=False)
Db = Annotated[Session, Depends(get_db)]


@app.on_event("startup")
def create_tables() -> None:
    # The MVP creates its small schema automatically. Use Alembic before evolving
    # the schema for a deployed production service.
    Base.metadata.create_all(bind=engine)
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS source_company VARCHAR(180)"))
        connection.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS source_url VARCHAR(1000)"))
    seed_astana_hub_tasks()


ASTANAHUB_TASKS = [
    {
        "source_company": "ТОО iDerek",
        "source_url": "https://astanahub.com/en/tech_task/ocr-na-khostinge",
        "title": "Локальный OCR PDF-сканов на собственном хостинге",
        "description": (
            "В сервисе проверки документов часть PDF-сканов распознаётся внешним AI-сервисом. "
            "Нужно подготовить автономный модуль для обычных печатных документов на русском и казахском: "
            "на входе PDF, на выходе точный UTF-8 текст в порядке чтения. Сложные бланки и рукописный текст не входят "
            "в описанный объём. Интеграция предполагается с PHP-приложением через локальный CLI или HTTP-сервис."
        ),
        "industry": "Обработка данных и OCR",
        "target_users": "Сервис ТОО iDerek для проверки пакетов документов для государственных услуг Казахстана.",
        "available_data": (
            "В исходной карточке указано, что для бенчмарка предоставят около 150–200 обезличенных PDF на русском и казахском "
            "с эталонным текстом."
        ),
        "success_criteria": (
            "Сравнить CER/WER с эталонным текстом и точность критичных полей. По исходной карточке, качество должно быть не хуже "
            "указанного там baseline Gemini 2.5 Flash; обработка — полностью локальная."
        ),
        "deadline": "Срок принятия решений на Astana Hub — 29.09.2026; срок сдачи результата — 01.10.2026.",
        "tags": ["OCR", "PDF", "русский и казахский", "Tesseract", "OpenCV"],
    },
    {
        "source_company": "Xena Soft",
        "source_url": "https://astanahub.com/en/tech_task/ii-agent-dlia-soprovozhdeniia-skvoznykh-avtotestov-v-ci-razbor-padenii-ispravlenie-testov-i-rasshirenie",
        "title": "AI-агент для сопровождения E2E-тестов в CI",
        "description": (
            "Сделать переносимого агента для Playwright E2E-тестов: разбирать падения, различать проблемы теста, продукта и инфраструктуры, "
            "поддерживать тесты и расширять покрытие. Изменения кода оформляются как PR/MR для проверки человеком. "
            "В описании проекта названы адаптеры для GitHub Actions, GitLab CI и Azure DevOps, а также история прогонов и метрики."
        ),
        "industry": "Разработка ПО и автоматизация тестирования",
        "target_users": "Команды Xena Soft, сопровождающие веб-продукты и их сквозные тесты.",
        "available_data": (
            "В исходной карточке указаны два действующих прототипа на проектах с Azure DevOps Pipelines и GitHub Actions. "
            "Обезличенную копию прототипа обещают выбранному исполнителю после NDA."
        ),
        "success_criteria": (
            "Среди ориентиров исходной карточки: до 60 минут от артефактов падения до PR/MR для поддерживаемых сбоев; "
            "классификация каждого прогона; подключение подходящего проекта за один рабочий день."
        ),
        "deadline": "Срок принятия решений на Astana Hub — 30.09.2026.",
        "tags": ["Python", "Playwright", "CI/CD", "GitHub Actions", "GitLab CI", "Azure DevOps"],
    },
    {
        "source_company": "ТОО \"PROMAT-SYSTEMS\"",
        "source_url": "https://astanahub.com/en/tech_task/ustoichivoe-nochnoe-raspoznavanie-gosnomerov-rk-na-vezde-parkovki-ik-podsvetka-zasvetka-farami-raz",
        "title": "Ночное распознавание госномеров на парковке",
        "description": (
            "Повысить стабильность распознавания казахстанских госномеров ночью на въезде парковки с обычной IP-камерой. "
            "В исходном описании проблемы перечислены засветка фарами, смазывание, шум и блики ИК-подсветки; "
            "нужно исследовать обработку кадра/OCR и настройки камеры."
        ),
        "industry": "Парковки и интеллектуальные системы управления",
        "target_users": "Операторы парковок и водители, использующие автоматический въезд Promat Parking.",
        "available_data": (
            "Одна обычная IP-камера 4 Мп установлена у въезда; исходная карточка указывает, что записи с госномерами "
            "могут быть переданы после подписания NDA. Пилот описан для действующего объекта в Астане."
        ),
        "success_criteria": (
            "Цель, указанная в исходной карточке: ночная точность распознавания не ниже 95% и автоматический въезд без оператора. "
            "Сейчас в карточке приведено около 87% ночью против 98% днём."
        ),
        "deadline": "Срок принятия решений на Astana Hub — 05.10.2026.",
        "tags": ["Computer Vision", "OCR", "OpenCV", "IP-камера", "ИК-подсветка"],
    },
]


def seed_astana_hub_tasks() -> None:
    """Import source-linked snapshots under one clearly local review account."""
    email = os.getenv("ASTANAHUB_REVIEW_EMAIL", "catalog@aisana.example.com").strip().lower()
    password = os.getenv("ASTANAHUB_REVIEW_PASSWORD", "local-demo-change-me")
    with SessionLocal() as db:
        user = db.scalar(select(User).options(joinedload(User.company_profile)).where(User.email == email))
        if user is None and email == "catalog@aisana.example.com":
            user = db.scalar(
                select(User).options(joinedload(User.company_profile)).where(User.email == "catalog@aisana.local")
            )
            if user:
                user.email = email
                user.password_hash = hash_password(password)
        if user is None:
            user = User(
                email=email,
                name="Локальный куратор каталога",
                password_hash=hash_password(password),
                role="company",
                company_profile=CompanyProfile(company_name="AI Sana · импорт Astana Hub (локальная копия)"),
            )
            db.add(user)
            db.flush()
        if user.role != "company":
            raise RuntimeError("ASTANAHUB_REVIEW_EMAIL must belong to a company account.")
        if user.company_profile is None:
            user.company_profile = CompanyProfile(company_name="AI Sana · импорт Astana Hub (локальная копия)")
        existing_urls = set(db.scalars(select(Task.source_url).where(Task.source_url.is_not(None))).all())
        for entry in ASTANAHUB_TASKS:
            if entry["source_url"] in existing_urls:
                db.query(Task).filter(Task.source_url == entry["source_url"]).update({"owner_id": user.id})
                continue
            task_data = {key: value for key, value in entry.items() if key not in {"source_company", "source_url"}}
            db.add(
                Task(
                    owner_id=user.id,
                    status="published",
                    source_company=entry["source_company"],
                    source_url=entry["source_url"],
                    **task_data,
                )
            )
        db.commit()


def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Db,
) -> User | None:
    if credentials is None:
        return None
    try:
        user_id = read_access_token(credentials.credentials)
    except (jwt.InvalidTokenError, ValueError, KeyError):
        raise HTTPException(status_code=401, detail="Сессия недействительна. Войдите снова.")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден.")
    return user


def get_current_user(user: Annotated[User | None, Depends(get_optional_user)]) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="Войдите в аккаунт, чтобы продолжить.")
    return user


def require_role(user: User, role: str) -> None:
    if user.role != role:
        raise HTTPException(status_code=403, detail="Для этого действия нужна другая роль.")


def user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        company_name=user.company_profile.company_name if user.company_profile else None,
    )


READINESS_FIELDS = [
    ("title", "Название задачи", 10, "Коротко обозначьте, что нужно сделать."),
    ("description", "Описание проблемы", 25, "Опишите контекст, проблему и ожидаемый результат."),
    ("industry", "Отрасль", 10, "Укажите сферу, чтобы задачу было проще найти."),
    ("target_users", "Для кого решается задача", 10, "Назовите пользователей или процесс, для которого ищется решение."),
    ("available_data", "Доступные данные или ресурсы", 15, "Перечислите только ресурсы, которые действительно можно предоставить."),
    ("success_criteria", "Критерии успеха", 20, "Опишите, по каким признакам компания оценит результат."),
    ("deadline", "Сроки", 5, "Укажите ожидаемый срок или дату."),
    ("tags", "Теги", 5, "Добавьте технологии и навыки, нужные для поиска команды."),
]


def readiness_details(task: Task) -> tuple[int, str, list[str], list[ReadinessFieldOut]]:
    breakdown = []
    for key, label, weight, guidance in READINESS_FIELDS:
        value = ",".join(task.tags or []) if key == "tags" else getattr(task, key, "")
        present = bool(value and value.strip())
        breakdown.append(
            ReadinessFieldOut(
                key=key,
                label=label,
                weight=weight,
                points=weight if present else 0,
                present=present,
                guidance=guidance,
            )
        )
    score = sum(item.points for item in breakdown)
    missing = [item.label for item in breakdown if not item.present]
    label = "Высокая" if score >= 85 else "Хорошая" if score >= 65 else "Базовая" if score >= 40 else "Черновик"
    return score, label, missing, breakdown


def readiness(task: Task) -> tuple[int, str, list[str]]:
    score, label, missing, _ = readiness_details(task)
    return score, label, missing


def task_out(db: Session, task: Task) -> TaskOut:
    score, label, missing, breakdown = readiness_details(task)
    count = db.scalar(select(func.count(Application.id)).where(Application.task_id == task.id)) or 0
    company_name = task.source_company or (task.owner.company_profile.company_name if task.owner.company_profile else "Компания")
    return TaskOut(
        id=task.id,
        owner_id=task.owner_id,
        company_name=company_name,
        source_url=task.source_url,
        is_imported=bool(task.source_url),
        title=task.title,
        description=task.description,
        industry=task.industry,
        target_users=task.target_users,
        available_data=task.available_data,
        success_criteria=task.success_criteria,
        deadline=task.deadline,
        tags=task.tags or [],
        status=task.status,
        readiness_score=score,
        readiness_label=label,
        missing_fields=missing,
        readiness_breakdown=breakdown,
        applications_count=count,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def application_out(application: Application) -> ApplicationOut:
    company = application.task.owner.company_profile.company_name if application.task.owner.company_profile else None
    return ApplicationOut(
        id=application.id,
        task_id=application.task_id,
        task_title=application.task.title,
        team_id=application.team_id,
        team_name=application.team.name,
        submitted_by_name=application.submitter.name,
        pitch=application.pitch,
        prototype_url=application.prototype_url,
        status=application.status,
        created_at=application.created_at,
        company_name=company,
    )


def team_out(db: Session, team: Team, current_user: User) -> TeamOut:
    members = db.scalars(
        select(TeamMember).options(joinedload(TeamMember.user)).where(TeamMember.team_id == team.id)
    ).all()
    return TeamOut(
        id=team.id,
        name=team.name,
        invite_code=team.invite_code if current_user.id in {member.user_id for member in members} else "",
        is_owner=team.created_by == current_user.id,
        members=[TeamMemberOut(user_id=member.user_id, name=member.user.name, email=member.user.email) for member in members],
    )


@app.get("/health")
def health(db: Db) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except OperationalError:
        raise HTTPException(status_code=503, detail="Не удаётся подключиться к PostgreSQL.")
    return {"status": "ok", "database": "connected"}


@app.post("/auth/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterInput, db: Db) -> TokenOut:
    email = str(payload.email).lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Аккаунт с таким email уже существует.")
    if payload.role == "company" and not (payload.company_name or "").strip():
        raise HTTPException(status_code=422, detail="Укажите название компании.")

    user = User(email=email, name=payload.name.strip(), password_hash=hash_password(payload.password), role=payload.role)
    db.add(user)
    if payload.role == "company":
        user.company_profile = CompanyProfile(company_name=payload.company_name.strip())
    try:
        db.flush()
        if payload.role == "student" and payload.team_name and payload.team_name.strip():
            team = Team(name=payload.team_name.strip(), invite_code=secrets.token_urlsafe(8).upper(), created_by=user.id)
            db.add(team)
            db.flush()
            db.add(TeamMember(team_id=team.id, user_id=user.id))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Не удалось создать аккаунт с указанными данными.")
    db.refresh(user)
    return TokenOut(access_token=create_access_token(user.id), user=user_out(user))


@app.post("/auth/login", response_model=TokenOut)
def login(payload: LoginInput, db: Db) -> TokenOut:
    user = db.scalar(select(User).options(joinedload(User.company_profile)).where(User.email == str(payload.email).lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный email или пароль.")
    return TokenOut(access_token=create_access_token(user.id), user=user_out(user))


@app.get("/auth/me", response_model=UserOut)
def me(user: Annotated[User, Depends(get_current_user)]) -> UserOut:
    return user_out(user)


@app.get("/tasks", response_model=list[TaskOut])
def list_tasks(
    db: Db,
    q: str = "",
    industry: str = "",
    min_score: int = Query(default=0, ge=0, le=100),
    sort: str = Query(default="newest", pattern="^(newest|score_asc|score_desc)$"),
    limit: int = Query(default=100, ge=1, le=200),
) -> list[TaskOut]:
    statement = (
        select(Task)
        .options(joinedload(Task.owner).joinedload(User.company_profile))
        .where(Task.status == "published")
    )
    if industry.strip():
        statement = statement.where(func.lower(Task.industry) == industry.strip().lower())
    if q.strip():
        pattern = f"%{q.strip()}%"
        statement = statement.where(
            Task.title.ilike(pattern)
            | Task.description.ilike(pattern)
            | Task.industry.ilike(pattern)
            | Task.tags.cast(String).ilike(pattern)
        )
    tasks = list(db.scalars(statement.order_by(Task.created_at.desc())).unique().all())
    tasks = [task for task in tasks if readiness(task)[0] >= min_score]
    if sort == "score_asc":
        tasks.sort(key=lambda item: readiness(item)[0])
    elif sort == "score_desc":
        tasks.sort(key=lambda item: readiness(item)[0], reverse=True)
    return [task_out(db, task) for task in tasks[:limit]]


@app.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Db) -> TaskOut:
    task = db.scalar(
        select(Task)
        .options(joinedload(Task.owner).joinedload(User.company_profile))
        .where(Task.id == task_id, Task.status == "published")
    )
    if not task:
        raise HTTPException(status_code=404, detail="Опубликованная задача не найдена.")
    return task_out(db, task)


@app.get("/company/tasks", response_model=list[TaskOut])
def my_company_tasks(db: Db, user: Annotated[User, Depends(get_current_user)]) -> list[TaskOut]:
    require_role(user, "company")
    tasks = db.scalars(
        select(Task)
        .options(joinedload(Task.owner).joinedload(User.company_profile))
        .where(Task.owner_id == user.id)
        .order_by(Task.updated_at.desc())
    ).unique().all()
    return [task_out(db, task) for task in tasks]


@app.post("/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskInput, db: Db, user: Annotated[User, Depends(get_current_user)]) -> TaskOut:
    require_role(user, "company")
    task = Task(owner_id=user.id, status="draft", **payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task_out(db, task)


def get_owned_task(db: Session, task_id: int, user: User) -> Task:
    task = db.scalar(
        select(Task).options(joinedload(Task.owner).joinedload(User.company_profile)).where(Task.id == task_id)
    )
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена.")
    if task.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Можно изменять только свои задачи.")
    if task.status == "closed":
        raise HTTPException(status_code=409, detail="Закрытую задачу нельзя изменить.")
    return task


@app.put("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: TaskInput, db: Db, user: Annotated[User, Depends(get_current_user)]) -> TaskOut:
    require_role(user, "company")
    task = get_owned_task(db, task_id, user)
    if task.source_url:
        raise HTTPException(status_code=409, detail="Карточку из внешнего каталога нельзя редактировать. Откройте исходную публикацию по ссылке.")
    for key, value in payload.model_dump().items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return task_out(db, task)


@app.post("/tasks/{task_id}/publish", response_model=TaskOut)
def publish_task(task_id: int, db: Db, user: Annotated[User, Depends(get_current_user)]) -> TaskOut:
    require_role(user, "company")
    task = get_owned_task(db, task_id, user)
    required = {
        "Описание проблемы": task.description,
        "Отрасль": task.industry,
        "Для кого решается задача": task.target_users,
        "Доступные данные или ресурсы": task.available_data,
        "Критерии успеха": task.success_criteria,
        "Сроки": task.deadline,
    }
    missing = [name for name, value in required.items() if not value or not value.strip()]
    if missing:
        raise HTTPException(status_code=422, detail="Заполните обязательные поля: " + ", ".join(missing))
    task.status = "published"
    db.commit()
    db.refresh(task)
    return task_out(db, task)


@app.post("/tasks/{task_id}/close", response_model=TaskOut)
def close_task(task_id: int, db: Db, user: Annotated[User, Depends(get_current_user)]) -> TaskOut:
    require_role(user, "company")
    task = get_owned_task(db, task_id, user)
    task.status = "closed"
    db.commit()
    db.refresh(task)
    return task_out(db, task)


@app.get("/teams/mine", response_model=list[TeamOut])
def my_teams(db: Db, user: Annotated[User, Depends(get_current_user)]) -> list[TeamOut]:
    require_role(user, "student")
    teams = db.scalars(
        select(Team).join(TeamMember).where(TeamMember.user_id == user.id).order_by(Team.created_at.desc())
    ).unique().all()
    return [team_out(db, team, user) for team in teams]


@app.post("/teams", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
def create_team(payload: TeamCreateInput, db: Db, user: Annotated[User, Depends(get_current_user)]) -> TeamOut:
    require_role(user, "student")
    team = Team(name=payload.name.strip(), invite_code=secrets.token_urlsafe(8).upper(), created_by=user.id)
    db.add(team)
    db.flush()
    db.add(TeamMember(team_id=team.id, user_id=user.id))
    db.commit()
    db.refresh(team)
    return team_out(db, team, user)


@app.post("/teams/join", response_model=TeamOut)
def join_team(payload: TeamJoinInput, db: Db, user: Annotated[User, Depends(get_current_user)]) -> TeamOut:
    require_role(user, "student")
    code = payload.invite_code.strip().upper()
    team = db.scalar(select(Team).where(func.upper(Team.invite_code) == code))
    if not team:
        raise HTTPException(status_code=404, detail="Команда с таким кодом не найдена.")
    if db.scalar(select(TeamMember.id).where(TeamMember.team_id == team.id, TeamMember.user_id == user.id)):
        return team_out(db, team, user)
    db.add(TeamMember(team_id=team.id, user_id=user.id))
    db.commit()
    return team_out(db, team, user)


@app.post("/tasks/{task_id}/applications", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
def submit_application(
    task_id: int,
    payload: ApplicationCreateInput,
    db: Db,
    user: Annotated[User, Depends(get_current_user)],
) -> ApplicationOut:
    require_role(user, "student")
    task = db.scalar(
        select(Task)
        .options(joinedload(Task.owner).joinedload(User.company_profile))
        .where(Task.id == task_id, Task.status == "published")
    )
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена или уже закрыта.")
    membership = db.scalar(
        select(TeamMember).where(TeamMember.team_id == payload.team_id, TeamMember.user_id == user.id)
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Можно откликаться только от команды, в которой вы состоите.")
    if db.scalar(select(Application.id).where(Application.task_id == task_id, Application.team_id == payload.team_id)):
        raise HTTPException(status_code=409, detail="Эта команда уже отправила отклик на задачу.")
    application = Application(
        task_id=task_id,
        team_id=payload.team_id,
        submitted_by=user.id,
        pitch=payload.pitch.strip(),
        prototype_url=str(payload.prototype_url) if payload.prototype_url else "",
        status="submitted",
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    application = db.scalar(
        select(Application)
        .options(joinedload(Application.task).joinedload(Task.owner).joinedload(User.company_profile), joinedload(Application.team), joinedload(Application.submitter))
        .where(Application.id == application.id)
    )
    return application_out(application)


@app.get("/applications/mine", response_model=list[ApplicationOut])
def my_applications(db: Db, user: Annotated[User, Depends(get_current_user)]) -> list[ApplicationOut]:
    require_role(user, "student")
    team_ids = select(TeamMember.team_id).where(TeamMember.user_id == user.id)
    applications = db.scalars(
        select(Application)
        .options(joinedload(Application.task).joinedload(Task.owner).joinedload(User.company_profile), joinedload(Application.team), joinedload(Application.submitter))
        .where(Application.team_id.in_(team_ids))
        .order_by(Application.created_at.desc())
    ).unique().all()
    return [application_out(application) for application in applications]


@app.get("/tasks/{task_id}/applications", response_model=list[ApplicationOut])
def task_applications(
    task_id: int,
    db: Db,
    user: Annotated[User, Depends(get_current_user)],
) -> list[ApplicationOut]:
    require_role(user, "company")
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена.")
    if task.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Просматривать можно только отклики на свои задачи.")
    applications = db.scalars(
        select(Application)
        .options(joinedload(Application.task).joinedload(Task.owner).joinedload(User.company_profile), joinedload(Application.team), joinedload(Application.submitter))
        .where(Application.task_id == task_id)
        .order_by(Application.created_at.desc())
    ).unique().all()
    return [application_out(application) for application in applications]


def owned_application(db: Session, application_id: int, user: User) -> Application:
    application = db.scalar(
        select(Application)
        .options(joinedload(Application.task), joinedload(Application.team), joinedload(Application.submitter))
        .where(Application.id == application_id)
    )
    if not application:
        raise HTTPException(status_code=404, detail="Отклик не найден.")
    if application.task.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Можно менять статус только откликов на свои задачи.")
    if application.task.status == "closed":
        raise HTTPException(status_code=409, detail="Задача уже закрыта.")
    return application


@app.post("/applications/{application_id}/review", response_model=ApplicationOut)
def review_application(
    application_id: int,
    db: Db,
    user: Annotated[User, Depends(get_current_user)],
) -> ApplicationOut:
    require_role(user, "company")
    application = owned_application(db, application_id, user)
    if application.status not in {"submitted", "reviewing"}:
        raise HTTPException(status_code=409, detail="Этот отклик уже получил окончательное решение.")
    application.status = "reviewing"
    db.commit()
    db.refresh(application)
    application = db.scalar(
        select(Application)
        .options(joinedload(Application.task).joinedload(Task.owner).joinedload(User.company_profile), joinedload(Application.team), joinedload(Application.submitter))
        .where(Application.id == application_id)
    )
    return application_out(application)


@app.post("/applications/{application_id}/reject", response_model=ApplicationOut)
def reject_application(
    application_id: int,
    db: Db,
    user: Annotated[User, Depends(get_current_user)],
) -> ApplicationOut:
    require_role(user, "company")
    application = owned_application(db, application_id, user)
    if application.status not in {"submitted", "reviewing"}:
        raise HTTPException(status_code=409, detail="Этот отклик уже получил окончательное решение.")
    application.status = "rejected"
    db.commit()
    application = db.scalar(
        select(Application)
        .options(joinedload(Application.task).joinedload(Task.owner).joinedload(User.company_profile), joinedload(Application.team), joinedload(Application.submitter))
        .where(Application.id == application_id)
    )
    return application_out(application)


@app.post("/applications/{application_id}/accept", response_model=ApplicationOut)
def accept_application(
    application_id: int,
    db: Db,
    user: Annotated[User, Depends(get_current_user)],
) -> ApplicationOut:
    require_role(user, "company")
    application = owned_application(db, application_id, user)
    task = application.task
    if application.status not in {"submitted", "reviewing"}:
        raise HTTPException(status_code=409, detail="Этот отклик уже получил окончательное решение.")
    application.status = "accepted"
    task.status = "closed"
    other_applications = db.scalars(
        select(Application).where(Application.task_id == task.id, Application.id != application.id)
    ).all()
    for other in other_applications:
        if other.status in {"submitted", "reviewing"}:
            other.status = "rejected"
    db.commit()
    application = db.scalar(
        select(Application)
        .options(joinedload(Application.task).joinedload(Task.owner).joinedload(User.company_profile), joinedload(Application.team), joinedload(Application.submitter))
        .where(Application.id == application_id)
    )
    return application_out(application)


@app.post("/ai/improve-task", response_model=TaskAssistOutput)
async def improve_task(
    payload: TaskAssistInput,
    user: Annotated[User, Depends(get_current_user)],
) -> TaskAssistOutput:
    require_role(user, "company")
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=503, detail="AI-помощник отключён: добавьте OPENAI_API_KEY в .env и перезапустите приложение.")

    source = payload.model_dump()
    source_fields = {key: value.strip() for key, value in source.items() if value and value.strip()}
    if not source_fields:
        raise HTTPException(status_code=422, detail="Сначала заполните хотя бы одно поле задачи.")
    field_names = ["title", "description", "industry", "target_users", "available_data", "success_criteria", "deadline"]
    instructions = (
        "Ты редактор описаний задач для учебного проекта. Верни только JSON-объект с ключами "
        + ", ".join(field_names)
        + ". Перефразируй только непустые исходные поля, сохраняя смысл и все факты. Не добавляй числа, сроки, названия, данные, ограничения, обещания или сведения, которых нет в исходном тексте. "
        "Если поле пустое, верни для него пустую строку. Не заполняй пробелы догадками. Если исходный текст уже ясен, верни его без изменений."
    )
    request_body = {
        "model": os.getenv("OPENAI_MODEL", "gpt-5-mini"),
        "store": False,
        "instructions": instructions,
        "input": json.dumps(source, ensure_ascii=False),
        "text": {"format": {"type": "json_object"}},
    }
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(
                "https://api.openai.com/v1/responses",
                headers={"Authorization": f"Bearer {api_key}"},
                json=request_body,
            )
        if response.is_error:
            raise HTTPException(status_code=502, detail="AI-провайдер не принял запрос. Проверьте API-ключ и модель.")
        body = response.json()
        output_text = "".join(
            item.get("text", "")
            for item in body.get("output", [])
            if item.get("type") == "message"
            for item in item.get("content", [])
            if item.get("type") == "output_text"
        )
        result = json.loads(output_text)
    except HTTPException:
        raise
    except (httpx.HTTPError, ValueError, TypeError):
        raise HTTPException(status_code=502, detail="Не удалось получить корректное предложение от AI.")

    suggestions: dict[str, str] = {}
    for field in field_names:
        candidate = result.get(field)
        original = source_fields.get(field, "")
        if not original or not isinstance(candidate, str) or not candidate.strip():
            continue
        candidate = candidate.strip()[:10000]
        candidate_numbers = set(re.findall(r"\d+(?:[.,]\d+)?", candidate))
        original_numbers = set(re.findall(r"\d+(?:[.,]\d+)?", original))
        if candidate_numbers.issubset(original_numbers):
            suggestions[field] = candidate
    return TaskAssistOutput(
        suggestions=suggestions,
        note="AI предложил редактуру только для заполненных полей. Проверьте смысл и примените изменения вручную.",
    )
>>>>>>> feature/Branch-raiymbek
