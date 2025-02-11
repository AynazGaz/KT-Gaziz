"""
Установка FastAPI и Uvicorn: pip install fastapi uvicorn
Установка PIL: pip install pillow
Чтобы запустить cv2, необходимо установить библиотеку OpenCV: pip install opencv-python
    Запуск сервера     uvicorn main:app --reload
PUT /upload/: Загрузка файлов на сервер.
GET /download/{file_id}: Скачивание файлов с сервера.
GET /preview/{file_id}: Получение превью с указанными шириной и высотой.
Открываем страницу http://localhost:8000/docs после запуска сервера

Добавили для бд:
    Модель MediaFile:
Хранит информацию о файле: UUID, путь, тип, размер и время загрузки.
    База данных:
Используется SQLite для простоты (файл database.db).
Таблицы создаются автоматически при запуске приложения.
    Работа с базой данных:
При загрузке файла информация сохраняется в базу данных.
При скачивании или получении превью данные берутся из базы данных.
    Сохранение превью:
Превью сохраняются в папку previews с именем в формате {file_id}_{width}x{height}.png.

"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlmodel import Session
from models import MediaFile
from database import engine, get_db, create_db_and_tables
from datetime import datetime
import os
import uuid

app = FastAPI()

# Папки для хранения файлов и превью
UPLOAD_DIRECTORY = "uploads"
PREVIEW_DIRECTORY = "previews"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
os.makedirs(PREVIEW_DIRECTORY, exist_ok=True)

# Создание таблиц при запуске приложения
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Обработчик для корневого пути
@app.get("/")
def read_root():
    return {"message": "Welcome to the File Upload and Download API!"}

# Загрузка файла
@app.put("/upload/")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_uuid = str(uuid.uuid4())
    file_extension = file.filename.split(".")[-1]

    if file_extension not in ["png", "jpg", "jpeg", "mp4", "avi"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    file_path = os.path.join(UPLOAD_DIRECTORY, f"{file_uuid}.{file_extension}")
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    file_size = os.path.getsize(file_path)
    file_type = "IMG" if file_extension in ["png", "jpg", "jpeg"] else "VID"

    # Сохранение информации о файле в базу данных
    media_file = MediaFile(
        id=file_uuid,
        file_path=file_path,
        file_type=file_type,
        file_size=file_size,
        created_at=datetime.utcnow()
    )
    db.add(media_file)
    db.commit()
    db.refresh(media_file)

    return {"message": "File uploaded successfully", "file_id": file_uuid}

# Скачивание файла
@app.get("/download/{file_id}")
async def download_file(file_id: str, db: Session = Depends(get_db)):
    media_file = db.get(MediaFile, file_id)
    if not media_file:
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(media_file.file_path)

# Получение превью
@app.get("/preview/{file_id}")
async def get_preview(file_id: str, width: int, height: int, db: Session = Depends(get_db)):
    media_file = db.get(MediaFile, file_id)
    if not media_file:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = media_file.file_path
    file_extension = file_path.split(".")[-1]

    preview_path = os.path.join(PREVIEW_DIRECTORY, f"{file_id}_{width}x{height}.png")

    if os.path.exists(preview_path):
        return FileResponse(preview_path)

    if file_extension in ["png", "jpg", "jpeg"]:
        from PIL import Image
        with Image.open(file_path) as img:
            img = img.resize((width, height))
            img.save(preview_path, format="PNG")
            return FileResponse(preview_path)

    elif file_extension in ["mp4", "avi"]:
        import cv2
        cap = cv2.VideoCapture(file_path)
        success, frame = cap.read()
        cap.release()
        if not success:
            raise HTTPException(status_code=500, detail="Failed to capture video frame")

        frame = cv2.resize(frame, (width, height))
        cv2.imwrite(preview_path, frame)
        return FileResponse(preview_path)

    raise HTTPException(status_code=400, detail="Unsupported file type")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)