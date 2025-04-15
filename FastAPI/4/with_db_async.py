import asyncio
import json
import logging
import time
from typing import Sequence

import aiofiles
import httpx
from fastapi import FastAPI, HTTPException
from sqlalchemy import Column, Integer, MetaData, Select, String, Table
from sqlalchemy.engine.row import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

# pylint: disable=logging-fstring-interpolation

# конфігурація логування і створення логера для модуля
logging.basicConfig(
    style="{",
    level=logging.INFO,
    handlers=(logging.StreamHandler(),),
    datefmt="%Y-%m-%d %H:%M:%S",
    format="[{levelname} - {asctime}] - {name} - {message}",
)
logger = logging.getLogger(__name__)

# драйвер 'aiosqlite' необхідний для асинхронної роботи
DATABASE_URL = "sqlite+aiosqlite:///./test_async.db"

# створення екземпляра Engine для БД
# створення асинхронної сесії (глобальної)
# при 'commit' вона продовжує існувати (це необхідно)
# 'metadata' зберігає дані про таблицю (її поля, типи даних і т.д.)
engine = create_async_engine(DATABASE_URL)
async_session = AsyncSession(engine, expire_on_commit=False)
metadata = MetaData()

# створення таблиці за допомогою синтаксису SQLAlchemy
users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(30)),
    Column("email", String(50)),
)


async def simulate_io_delay():
    """Симуляція затримки доступу до стороннього API."""
    start = time.perf_counter()
    async with httpx.AsyncClient() as client:
        logger.info("Start API request.")
        # асинхронний запит на сторонній API із затримкою
        # затримка 3 секунди, але сам сервіс робить ще якусь затримку
        # тому інколи є перевищення значення 'timeout' і запит може завершитись помилкою
        # просто треба заново зробити запит
        response = await client.get("https://httpbin.org/delay/3", timeout=6)

    end = time.perf_counter()
    logger.info(f"End API request in: {end - start:.5f} seconds.")
    return response.json()


async def get_users_from_db(
    query: Select, session: AsyncSession
) -> Sequence[RowMapping]:
    """Отримання всіх користувачів із БД."""
    start = time.perf_counter()
    logger.info("Start DB query.")

    # виконання запиту в БД та отримання всіх користувачів у вигляді словника
    # для цього використовується 'mappings()'
    cursor = await session.execute(query)
    all_users = cursor.mappings().all()
    end = time.perf_counter()

    logger.info(f"End DB query in {end - start:.5f} seconds.")

    # переключення на задачу запису користувачів в файл
    await write_users_to_file(all_users)
    return all_users


async def write_users_to_file(users: Sequence[RowMapping]) -> None:
    """Запис даних користувачів в текстовий файл."""
    start = time.perf_counter()
    logger.info("Start writing users to file.")

    # асинхронний запис списку користувачів в файл в необхідному форматі
    # бібліотека 'aiofiles' дозволяє це робити асинхронно
    async with aiofiles.open("users_async.txt", "w", encoding="utf-8") as fp:
        for user in users:
            # формат: "1. Jack (example@example.com)"
            await fp.write(f"{user['id']}. {user['name']} ({user['email']})\n")

    end = time.perf_counter()
    logger.info(f"End writing users to file in: {end - start:.5f} seconds.")


async def startup() -> None:
    """Створення таблиць в БД при старті програми."""
    async with engine.begin() as connection:
        # виконується запуск синхронної функції 'create_all'
        # асинхронним об'єктом з'єднання
        await connection.run_sync(metadata.create_all)


async def shutdown() -> None:
    """Закриття з'єднання з БД після завершення програми."""
    await engine.dispose()


# корутини 'on_startup' та 'on_shutdown' відповідно запускаються
# при запуску і при зупинці нашого обє'кту FastAPI
app = FastAPI(on_startup=[startup], on_shutdown=[shutdown], title="DB Async")


@app.post("/users/{user_name}/{user_email}")
async def create_user(user_name: str, email: str):
    """Створення користувача в БД з переданими іменем `user_name`."""
    query = users.select().where(users.c.email == email)

    # виконання запиту в БД за допомогою асинхронної глобальної сесії
    # та отримання лише одного запису
    cursor = await async_session.execute(query)
    existing_user = cursor.fetchone()

    if existing_user is not None:
        raise HTTPException(
            status_code=400, detail="User with this name already exists."
        )

    # додавання користувача в БД з іменем і поштою
    # та підтвердження запису через 'commit'
    query = users.insert().values(name=user_name, email=email)

    await async_session.execute(query)
    await async_session.commit()

    return {"user_name": user_name}


@app.get("/users/")
async def read_users():
    """Отримання всіх користувачів із БД."""
    start = time.perf_counter()
    query = users.select()

    # створення задач для асинхронного виконання операцій введення-виведення (а не одна за одною)
    delay_task = asyncio.create_task(simulate_io_delay())
    get_users_task = asyncio.create_task(get_users_from_db(query, async_session))

    # очікування виконання асинхронних задач та отримання результатів їх виконання
    # 'gather' додає всі задачі в 'event loop' і потім вони можуть переключатись між собою
    # поки одна задача очікує якусь відповідь (з БД, наприклад) - працює інша задач
    # результати задач будуть відповідно до розміщення їх у 'gather' функції
    # 'delay_task' --> 'response' змінна, а 'get_users_task' --> 'all_users' змінна відповідно
    response, all_users = await asyncio.gather(delay_task, get_users_task)

    # отримання результату із стороннього API
    print(f"Data from API: {json.dumps(response, indent=2)}")

    logger.info(f"Затрачено часу: {time.perf_counter() - start:.2f} секунд.")
    return {"users": all_users}
