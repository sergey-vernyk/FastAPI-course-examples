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

logging.basicConfig(
    style="{",
    level=logging.INFO,
    handlers=(logging.StreamHandler(),),
    datefmt="%Y-%m-%d %H:%M:%S",
    format="[{levelname} - {asctime}] - {name} - {message}",
)
logger = logging.getLogger(__name__)

DATABASE_URL = "sqlite+aiosqlite:///./test_async.db"

engine = create_async_engine(DATABASE_URL)
async_session = AsyncSession(engine, expire_on_commit=False)
metadata = MetaData()

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

    cursor = await session.execute(query)
    all_users = cursor.mappings().all()
    end = time.perf_counter()

    logger.info(f"End DB query in {end - start:.5f} seconds.")
    await write_users_to_file(all_users)
    return all_users


async def write_users_to_file(users: Sequence[RowMapping]) -> None:
    """Запис даних користувачів в текстовий файл."""
    start = time.perf_counter()
    logger.info("Start writing users to file.")

    async with aiofiles.open("users_async.txt", "w", encoding="utf-8") as fp:
        for user in users:
            # формат: "1. Jack (example@example.com)"
            await fp.write(f"{user['id']}. {user['name']} ({user['email']})\n")

    end = time.perf_counter()
    logger.info(f"End writing users to file in: {end - start:.5f} seconds.")


async def startup() -> None:
    """Створення таблиць в БД при старті програми."""
    async with engine.begin() as connection:
        await connection.run_sync(metadata.create_all)


async def shutdown() -> None:
    """Закриття з'єднання з БД після завершення програми."""
    await engine.dispose()


app = FastAPI(on_startup=[startup], on_shutdown=[shutdown], title="DB Async")


@app.post("/users/{user_name}/{user_email}")
async def create_user(user_name: str, email: str):
    """Створення користувача в БД з переданими іменем `user_name`."""
    query = users.select().where(users.c.email == email)
    cursor = await async_session.execute(query)
    existing_user = cursor.fetchone()

    if existing_user is not None:
        raise HTTPException(
            status_code=400, detail="User with this name already exists."
        )
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
    response, all_users = await asyncio.gather(delay_task, get_users_task)

    # отримання результату із стороннього API
    print(f"Data from API: {json.dumps(response, indent=2)}")

    logger.info(f"Затрачено часу: {time.perf_counter() - start:.2f} секунд.")
    return {"users": all_users}
