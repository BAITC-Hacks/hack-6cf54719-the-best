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
