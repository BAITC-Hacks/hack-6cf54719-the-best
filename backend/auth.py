import hashlib
from datetime import datetime, timezone
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session
from .database import get_db
from .models import LoginSession, User

password_hash = PasswordHash.recommended()
oauth2 = OAuth2PasswordBearer(tokenUrl="auth/login")
DUMMY_HASH = password_hash.hash("unused-dummy-password")

def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def current_user(token: str = Depends(oauth2), db: Session = Depends(get_db)):
    session = db.get(LoginSession, token_digest(token))
    if session and session.expires_at > datetime.now(timezone.utc):
        user = db.get(User, session.user_id)
        if user:
            return user
    raise HTTPException(401, "Войдите в аккаунт", headers={"WWW-Authenticate": "Bearer"})

def require_roles(*roles):
    def check(user: User = Depends(current_user)):
        if user.role not in roles:
            raise HTTPException(403, "Недостаточно прав")
        return user
    return check
