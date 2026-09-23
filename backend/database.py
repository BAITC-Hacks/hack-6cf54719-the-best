import os
<<<<<<< HEAD
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
=======
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://aisana:aisana_dev_password@localhost:5432/aisana",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

>>>>>>> feature/Branch-raiymbek

class Base(DeclarativeBase):
    pass

<<<<<<< HEAD
engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    with SessionLocal() as session:
        yield session
=======

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
>>>>>>> feature/Branch-raiymbek
