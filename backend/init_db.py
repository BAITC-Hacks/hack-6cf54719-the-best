"""Первичное создание таблиц; существующие таблицы и данные не удаляются."""
from .database import Base, engine
from . import models  # Register tables with metadata.

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    print("Database tables are ready.")
