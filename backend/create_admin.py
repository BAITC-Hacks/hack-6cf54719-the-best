"""Создание первого администратора: python -m backend.create_admin."""
from getpass import getpass
from sqlalchemy import select
from .database import SessionLocal
from .models import User, Role
from .schemas import Register
from .auth import password_hash

def main():
    payload = Register(email=input("Email: ").strip(), name=input("Name: ").strip(),
                       password=getpass("Password (10+ characters): "))
    with SessionLocal() as db:
        email = str(payload.email).lower()
        if db.scalar(select(User).where(User.email == email)):
            raise SystemExit("Email already exists. Use an administrator to change the role.")
        db.add(User(email=email, name=payload.name, role=Role.admin,
                    password_hash=password_hash.hash(payload.password)))
        db.commit()
    print("Administrator created.")

if __name__ == "__main__":
    main()
