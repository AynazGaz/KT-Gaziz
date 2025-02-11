"""
Создадим модель для таблицы MediaFile, которая будет хранить информацию о файлах
"""

from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class MediaFile(SQLModel, table=True):
    id: str = Field(primary_key=True)  # Уникальный UUID файла
    file_path: str  # Путь к файлу на сервере
    file_type: str  # Тип файла: "IMG" или "VID"
    file_size: int  # Размер файла в байтах
    created_at: datetime = Field(default_factory=datetime.utcnow)  # Время загрузки файла