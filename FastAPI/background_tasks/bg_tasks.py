import asyncio
import pathlib
import random
import time

import aiofiles
import httpx
import pytest
import uvicorn
import yagmail
from fastapi import BackgroundTasks, FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

module_path = pathlib.Path(__file__).parent

# дані для відправки пошти з вашого акаунта Gmail
USER = "your_email_address"
PASSWORD = "your_password"

# pip install yagmail
yag = yagmail.SMTP(user=USER, password=PASSWORD)


async def send_email(email: str) -> None:
    """Відправлення листа на пошту `email` після реєстрації."""
    yag.send(
        to=email,
        subject="Registration complete",
        contents=f"Welcome to our site, '{email}'!",
    )


def sync_task(t: int) -> None:
    """
    Симуляція затримки виконання на `t` секунд
    з використанням блокуючої функції `time.sleep`.
    """
    time.sleep(t)
    print(f"{t} seconds passed.")


async def download_file_by_name(file_path: str) -> None:
    """Завантаження файлу великого розміру."""
    # для тестування завантаження файлу із іншого місця своєї файлової системи
    # в папку з цим модулем можна запустити свій сервер python через команду 'python3 -m http.server 8001 -b 127.0.0.1'
    # перейти в браузер за адресою http://127.0.0.1:8001 і знайти той файл, який треба завантажити
    async with httpx.AsyncClient() as client:
        response = await client.get(file_path)

    async with aiofiles.open(module_path / file_path, mode="wb") as fp:
        await fp.write(response.content)

    print(f"File '{file_path}' has been downloaded.")


async def simulate_io_delay() -> None:
    """Симуляція затримки доступу до стороннього API."""
    async with httpx.AsyncClient() as client:
        # асинхронний запит на сторонній API із затримкою
        # затримка 3 секунди, але сам сервіс робить ще якусь затримку
        # тому інколи є перевищення значення 'timeout' і запит може завершитись помилкою
        # просто треба заново зробити запит
        response = await client.get("https://httpbin.org/delay/3", timeout=10)
        print(response.json())


async def add_user_to_file(name: str, email: EmailStr, phone: str) -> None:
    """Запис даних нового користувача в текстовий файл."""
    # дістаємо всіх користувачів зі стороннього API
    async with httpx.AsyncClient() as client:
        response = await client.get("https://jsonplaceholder.typicode.com/users/")

    # та додаємо їх в файл
    async with aiofiles.open(module_path / "users.txt", "w", encoding="utf-8") as fp:
        for user in response.json():
            await fp.write(
                f"name = {user['name']} | email = {user['email']} | phone = {user['phone']}\n\n"
            )
        # додаємо дані нового користувача в файл
        await fp.write(f"name = {name} | email = {email} | phone = {phone}\n\n")


async def startup_event() -> None:
    """Створення асинхронної задачі для обробника асинхронної черги."""
    asyncio.create_task(process_task_queue())


app = FastAPI(title="Background Tasks", on_startup=(startup_event,))


class User(BaseModel):
    """Модель користувача."""

    name: str = Field(examples=["John", "Josh"])
    email: EmailStr = Field(examples=["john@example.com"])
    phone: str = Field(examples=["+380661234567"])


users_db: list[User] = []


@app.post("/register", status_code=status.HTTP_201_CREATED, response_model=User)
async def user_registration(user_data: User, bg_tasks: BackgroundTasks) -> User:
    """Реєстрацію користувача в базі даних."""
    if user_data.email in {u.email for u in users_db}:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "User exists.")

    users_db.append(user_data)

    bg_tasks.add_task(simulate_io_delay)
    bg_tasks.add_task(
        add_user_to_file,
        name=user_data.name,
        email=user_data.email,
        phone=user_data.phone,
    )
    # додаємо синхронну функцію в фонову задачу
    bg_tasks.add_task(send_email, user_data.email)

    # просто викликаємо функцію
    # розкоментувати для перевірки функції без фонової задачі
    # await send_email(user_data.email)

    # додаємо синхронну функцію в фонові задачі
    bg_tasks.add_task(sync_task, t=10)

    # просто викликаємо синхронну функцію
    # розкоментувати для перевірки функції без фонової задачі
    # sync_task(t=10)

    # відображення в консолі назви фонових задач та їх параметрів
    print([(task.func.__name__, task.args, task.kwargs) for task in bg_tasks.tasks])
    return User(**user_data.model_dump())


# глобальна асинхронна черга
task_queue = asyncio.Queue()


async def process_task_queue():
    """Обробка задач з черги."""
    while True:
        task = await task_queue.get()

        try:
            await task
        except asyncio.QueueShutDown as e:
            print(f"Getting task from a shut-down queue: {e}.")
        except asyncio.QueueEmpty as e:
            print(f"Getting task from an empty queue: {e}.")
        except Exception as e:
            print(f"Error while getting task from queue: {e}.")
        else:
            task_queue.task_done()

        if task_queue.empty():
            print("All tasks have been completed.")


async def run_task(name: str, delay: int) -> dict[str, str]:
    """Симуляція запуску задачі з іменем `name`та затримкою `delay`."""
    print(f"Task '{name}' with delay '{delay}' accepted.")
    await asyncio.sleep(delay)
    print(f"Task '{name}' is done in {delay} seconds.")
    return {"success": f"Task '{name}' is done in {delay} seconds."}


@app.post("/add-task/", status_code=status.HTTP_202_ACCEPTED)
async def add_task(name: str) -> dict[str, str]:
    """Додавання задачі в чергу."""
    await task_queue.put(run_task(name, random.randint(3, 10)))
    return {"message": f"Task '{name}' has been added to queue."}


@app.get("/download/", status_code=status.HTTP_202_ACCEPTED)
async def download_file(file_path: str, bg_tasks: BackgroundTasks) -> dict[str, str]:
    """Завантаження файлу на фоні."""
    # як знайти шлях до файлу описано в функції 'download_file_by_name'
    # потім скопіювати цю адресу і передати в SwaggerUI в параметр 'file_path'
    bg_tasks.add_task(download_file_by_name, file_path=file_path)
    return {"success": "File will be downloaded in the background."}


@pytest.mark.asyncio
async def test_add_task_to_queue() -> None:
    """Тест для перевірки додавання задачі в чергу."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://127.0.0.1:8000"
    ) as client:
        response = await client.post("/add-task/", params={"name": "hello"})

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {"message": "Task 'hello' has been added to queue."}
    # в черзі повинна бути лише одна задача
    assert task_queue.qsize() == 1


@pytest.mark.asyncio
async def test_run_task() -> None:
    """Тест для перевірки запуску задачі."""
    result = await run_task("hello", 3)
    assert result == {"success": "Task 'hello' is done in 3 seconds."}


@pytest.mark.asyncio
async def test_add_download_file() -> None:
    """Тест для перевірки завантаження файлу."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://127.0.0.1:8000"
    ) as client:
        response = await client.get(
            "/download/",
            # вкажіть свій шлях до файлу після запуску команди 'python3 -m http.server 8001 -b 127.0.0.1'
            params={"file_path": "http://127.0.0.1:8000/Desktop/test_large_file.bin"},
        )

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {"success": "File will be downloaded in the background."}


if __name__ == "__main__":
    uvicorn.run("bg_tasks:app", port=8000, reload=True)
