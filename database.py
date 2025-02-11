"""
Создадим файл database.py для настройки подключения к базе данных и создания таблиц
"""
from sqlmodel import create_engine, SQLModel, Session

# Настройка подключения к базе данных (SQLite)
DATABASE_URL = "sqlite:///database.db"

# Создание движка базы данных
engine = create_engine(DATABASE_URL, echo=True)

# Функция для создания таблиц
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Функция для получения сессии базы данных
def get_db():
    with Session(engine) as session:
        yield session