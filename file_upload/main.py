import pathlib
from io import BytesIO

import httpx
import pytest
import uvicorn
from fastapi import (
    BackgroundTasks,
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

# pip install pillow
from PIL import Image

# шлях до цього модуля в файловій системі
module_path = pathlib.Path(__file__).parent

# треба встановити тому, що завантажені файли надсилаються як 'form data'
# pip install python-multipart

app = FastAPI()


async def resize_image(img: bytes, fmt: str, size: tuple[int, int]) -> None:
    """Зміна розміру зображення та конвертація його в чорно-білий колір."""
    image = Image.open(BytesIO(img))
    image = image.convert("RGB").convert("L")
    resized_image = image.resize(size)
    save_path = module_path / f"resized_image_{size[0]}x{size[1]}.{fmt}"
    resized_image.save(save_path)
    print(f"Image saved to: {save_path}")


# curl -X 'POST' \
# 'http://127.0.0.1:8000/login/' \
#  -H 'accept: application/json' \
#  -H 'Content-Type: application/x-www-form-urlencoded' \
#  -d 'username=john%40example.com&password=password'
@app.post("/login/")
async def login(
    username: str = Form(examples=["john@example.com"]),
    password: str = Form(examples=["password"]),
):
    """Використання форм для передачі даних для логіну."""
    return {"username": username, "password": password}


# curl -X 'POST' \
#  'http://127.0.0.1:8000/save_file_from_bytes/' \
#  -H 'accept: application/json' \
#  -H 'Content-Type: multipart/form-data' \
#  -F 'file=@01 (1).jpg;type=image/jpeg'
@app.post("/upload_file_as_bytes/")
async def save_file_from_bytes(file: bytes = File(default=None)):
    """
    Збереження файлу в системі, який переданий в тілі запиту як байти
    через `multipart/form-data` тип контенту.
    """
    # в такому випадку весь контент файлу буде збережено в пам'яті
    # це буде добре працювати з невеликими файлами
    # для великих файлів це працює не оптимально

    # потрібно використовувати 'File', оскільки інакше параметри інтерпретуватимуться
    # як параметри запиту (query) або параметри тіла об'єктів (body) (JSON)

    # ім'я файлу не зберігається і файл може бути названий як завгодно
    with open(module_path / "picture_from_bytes.jpg", mode="wb") as fp:
        fp.write(file)

    return {"file_size": len(file)}


# curl -X 'POST' \
#  'http://127.0.0.1:8000/upload_file_as_file_obj/' \
#  -H 'accept: application/json' \
#  -H 'Content-Type: multipart/form-data' \
#  -F 'file=@01 (1).jpg;type=image/jpeg'
@app.post("/upload_file_as_file_obj/")
async def create_upload_file(file: UploadFile | None = None):
    """
    Збереження файлу в системі, який переданий
    через `multipart/form-data` тип контенту.
    """
    # Переваги в порівнянні з bytes:
    # 1) Не потрібно використовувати 'File()' у значенні параметра за замовчуванням.
    # 2) Використовується "буферизований" файл
    # 3) Файл зберігається в пам'яті до максимального розміру, і після перевищення цього ліміту він зберігається на диску.
    # 4) Це добре працюватиме для великих файлів, таких як зображення, відео, великі бінарні файли тощо, не витрачаючи всю пам'ять.
    # 5) Можна отримати метадані із завантаженого файлу.
    # 6) Має файлоподібний асинхронний інтерфейс.
    # 7) Надає фактичний об'єкт Python SpooledTemporaryFile, який можна передавати іншим бібліотекам, які очікують файлоподібний об'єкт.

    if file is not None:
        with open(module_path / "picture_upload_file.jpg", mode="wb") as fp:
            # await file.read() краще викликати в середині функції з async (корутина)
            # file.file.read() краще викликати в середині звичайної функції
            fp.write(await file.read())
            print(file.size)
            print(file.file.__sizeof__())

        return {
            "headers": file.headers,
            "file_size": file.size,
            "filename": file.filename,
        }

    return {"message": "No upload file sent."}


# curl -X 'POST' \
#  'http://127.0.0.1:8000/upload_multiple_images/' \
#  -H 'accept: application/json' \
#  -H 'Content-Type: multipart/form-data' \
#  -F 'description=For test!' \
#  -F 'images=@01 (1).jpg;type=image/jpeg' \
#  -F 'images=@1zgqoa.jpeg;type=image/jpeg' \
#  -F 'images=@01.jpg;type=image/jpeg'
@app.post("/upload_multiple_images/")
async def upload_multiple_images(
    images: list[UploadFile], description: str = Form(...)
):
    """Завантаження більше одного зображення разом з полем опису."""
    image_filenames = []

    # Дані з форм зазвичай кодуються за допомогою media type 'application/x-www-form-urlencoded',
    # коли вони не містять файлів, але коли форма містить файли, вона кодується як 'multipart/form-data'.
    # Якщо використовується 'File', FastAPI знатиме, що йому потрібно отримати файли з правильної частини тіла запиту.

    # Можна визначити кілька параметрів 'File' та 'Form' в операції зі шляхом (path param),
    # але також не можна визначити поля 'Body', які повинні бути отримані у форматі JSON,
    # оскільки тіло запиту буде закодовано з використанням 'multipart/form-data' замість 'application/json'.
    # Це не є обмеженням FastAPI, це частина протоколу HTTP.
    for image in images:
        with open(module_path / str(image.filename), mode="wb") as fp:
            # await file.read() краще викликати в середині функції з async (корутина)
            # file.file.read() краще викликати в середині звичайної функції
            fp.write(await image.read())
            image_filenames.append(image.filename)

    return {"description": description, "images": image_filenames}


MAX_IMAGE_SIZE = 1024 * 1024 * 10  # 10Mb
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png"}


# curl -X 'POST' \
#  'http://127.0.0.1:8000/check_file_attrs/?width=300&height=300' \
#  -H 'accept: application/json' \
#  -H 'Content-Type: multipart/form-data' \
#  -F 'file=@01.jpg;type=image/jpeg'
@app.post("/check_file_attrs/", status_code=status.HTTP_200_OK)
async def check_file_attrs(
    bg_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    width: int = 300,
    height: int = 300,
):
    """Завантаження файлу обмеженого по розміру і по формату."""
    if file.size > MAX_IMAGE_SIZE:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"File is too large. File size is {file.size} bytes.",
        )
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Unsupportable file format. {file.content_type} was received.",
        )

    # додаємо зміну розміру зображення в фонову задачу
    bg_tasks.add_task(
        resize_image,
        img=await file.read(),
        fmt=file.filename.split(".")[-1],
        size=(width, height),
    )

    return {"filename": file.filename, "size": file.size}


@pytest.mark.asyncio
async def test_upload_file_success() -> None:
    """Тестування успішного завантаження файлу зображення."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://127.0.0.1:8000"
    ) as client:
        with open(module_path / "test_file_supported_format.jpg", "rb") as f:
            # очікуваний розмір файлу в байтах
            expected_size = len(f.read())
            # необхідно повернутись на початку файлу для того, щоб його передати в запит
            # так як попередня команда прочитала файл повністю і курсор знаходиться в кінці файлу
            f.seek(0)
            response = await client.post(
                "/check_file_attrs/",
                files={"file": f},
                params={"width": 600, "height": 600},
            )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "filename": "test_file_supported_format.jpg",
        "size": expected_size,
    }


@pytest.mark.asyncio
async def test_upload_file_unsupported_format() -> None:
    """Тест на завантаження файлу зображення непідтримуваного формату."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://127.0.0.1:8000"
    ) as client:
        with open(module_path / "test_file_unsupported_format.webp", "rb") as f:
            response = await client.post("/check_file_attrs/", files={"file": f})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Unsupportable file format. image/webp was received."
    }


@pytest.mark.asyncio
async def test_upload_file_exceeds_size() -> None:
    """Тест на завантаження файлу зображення розмір якого перевищує максимальний допустимий."""
    # тимчасово змінюємо максимально допустимий розмір зображення
    global MAX_IMAGE_SIZE
    MAX_IMAGE_SIZE = 1024  # 1Kb

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://127.0.0.1:8000"
    ) as client:
        with open(module_path / "test_file_supported_format.jpg", "rb") as f:
            # очікуваний розмір файлу в байтах
            expected_size = len(f.read())
            # необхідно повернутись на початку файлу для того, щоб його передати в запит
            # так як попередня команда прочитала файл повністю і курсор знаходиться в кінці файлу
            f.seek(0)
            response = await client.post("/check_file_attrs/", files={"file": f})

    assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    assert response.json() == {
        "detail": f"File is too large. File size is {expected_size} bytes."
    }


if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)
