"""
Установка FastAPI и Uvicorn: pip install fastapi uvicorn
Установка PIL: pip install pillow
Чтобы запустить cv2, необходимо установить библиотеку OpenCV: pip install opencv-python
    Запуск сервера     uvicorn main:app --reload
PUT /upload/: Загрузка файлов на сервер.
GET /download/{file_id}: Скачивание файлов с сервера.
GET /preview/{file_id}: Получение превью с указанными шириной и высотой.

"""
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from PIL import Image
import cv2
import os
import uuid

app = FastAPI()
@app.get("/")
def read_root():
    return {"message": "Welcome to the File Upload and Download API!"}
# Папки для хранения файлов и превью
UPLOAD_DIRECTORY = "uploads"
PREVIEW_DIRECTORY = "previews"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
os.makedirs(PREVIEW_DIRECTORY, exist_ok=True)

# Обработчик для корневого пути
@app.get("/")
def read_root():
    return {"message": "Welcome to the File Upload and Download API!"}

@app.put("/upload/")
async def upload_file(file: UploadFile = File(...)):
    # Генерируем уникальный ID для файла
    file_uuid = str(uuid.uuid4())
    file_extension = file.filename.split(".")[-1]

    # Проверяем допустимые форматы файлов
    if file_extension not in ["png", "jpg", "jpeg", "mp4", "avi"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # Сохраняем файл на сервере
    file_path = os.path.join(UPLOAD_DIRECTORY, f"{file_uuid}.{file_extension}")
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    return {"message": "File uploaded successfully", "file_id": file_uuid}

@app.get("/download/{file_id}")
async def download_file(file_id: str):
    # Ищем файл по ID
    for file_name in os.listdir(UPLOAD_DIRECTORY):
        if file_name.startswith(file_id):
            file_path = os.path.join(UPLOAD_DIRECTORY, file_name)
            return FileResponse(file_path)

    # Если файл не найден
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/preview/{file_id}")
async def get_preview(file_id: str, width: int, height: int):
    # Ищем файл по ID
    for file_name in os.listdir(UPLOAD_DIRECTORY):
        if file_name.startswith(file_id):
            file_path = os.path.join(UPLOAD_DIRECTORY, file_name)
            file_extension = file_name.split(".")[-1]

            # Путь для сохранения превью
            preview_path = os.path.join(PREVIEW_DIRECTORY, f"{file_id}_{width}x{height}.png")

            # Если превью уже существует, возвращаем его
            if os.path.exists(preview_path):
                return FileResponse(preview_path)

            # Обработка изображений
            if file_extension in ["png", "jpg", "jpeg"]:
                with Image.open(file_path) as img:
                    img = img.resize((width, height))
                    img.save(preview_path, format="PNG")
                    return FileResponse(preview_path)

            # Обработка видео
            elif file_extension in ["mp4", "avi"]:
                cap = cv2.VideoCapture(file_path)
                success, frame = cap.read()
                cap.release()
                if not success:
                    raise HTTPException(status_code=500, detail="Failed to capture video frame")

                frame = cv2.resize(frame, (width, height))
                cv2.imwrite(preview_path, frame)
                return FileResponse(preview_path)

    # Если файл не найден
    raise HTTPException(status_code=404, detail="File not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)