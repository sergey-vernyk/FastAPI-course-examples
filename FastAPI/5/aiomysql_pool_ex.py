import asyncio
import os
from typing import Any

import aiomysql
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

# pylint: disable=logging-fstring-interpolation

# завантажуємо конфіденційні дані доступу до бази даних MySQL із файлу .env
load_dotenv(os.path.abspath(f"{os.path.pardir}/.env"))

MYSQL_CONNECTION_DATA = {
    "host": os.environ.get("MYSQL_HOST"),
    "port": int(os.environ.get("MYSQL_PORT", 3306)),
    "user": os.environ.get("MYSQL_USER"),
    "password": os.environ.get("MYSQL_PASSWORD"),
    "db": os.environ.get("MYSQL_DB"),
}


async def get_pool() -> aiomysql.Pool:
    """Створення пулу з'єднань до БД."""
    # поточний event loop можна не передавати як параметр до "aiomysql.connect"
    # в версії Python 3.10+
    loop = asyncio.get_event_loop()
    pool = await aiomysql.create_pool(**MYSQL_CONNECTION_DATA, loop=loop)
    return pool


async def shutdown() -> None:
    """Закриття пулу з'єднань з БД після завершення програми."""
    pool = await get_pool()
    pool.close()
    await pool.wait_closed()


app = FastAPI(title="DB Async aiomysql pool", on_shutdown=(shutdown,))


@app.post("/users/{user_name}/{user_email}")
async def create_user(user_name: str, email: str) -> dict[str, str]:
    """Створення користувача в БД з переданими іменем `user_name` та `email`."""
    pool = await get_pool()

    # отримуємо з'єднання з пулу
    async with pool.acquire() as connection:
        async with connection.cursor() as cur:
            await cur.execute("SELECT * FROM users WHERE email=%s", (email,))
            existing_user = await cur.fetchone()

    if existing_user is not None:
        raise HTTPException(
            status_code=400, detail="User with this name already exists."
        )

    # додаємо нового користувача
    async with pool.acquire() as connection:
        async with connection.cursor() as cur:
            await cur.execute(
                "INSERT INTO users (name, email) VALUES (%s, %s);", (user_name, email)
            )
            await connection.commit()

    return {"user_name": user_name}


@app.get("/users/")
async def read_users() -> dict[str, Any]:
    """Отримання всіх користувачів із БД."""
    pool = await get_pool()

    # отримуємо з'єднання з пулу і отримуємо всіх користувачів
    async with pool.acquire() as connection:
        async with connection.cursor() as cur:
            await cur.execute("SELECT * FROM users;")

    users = await cur.fetchall()

    return {"users": users}


@app.get("/users/{email}")
async def read_user(email: str) -> Any:
    """Отримання всіх користувачів із БД."""
    pool = await get_pool()

    # отримуємо з'єднання з пулу і отримуємо користувача по email
    async with pool.acquire() as connection:
        async with connection.cursor() as cur:
            await cur.execute("SELECT * FROM users WHERE email=%s;", (email,))

    user = await cur.fetchone()
    if user is None:
        raise HTTPException(
            status_code=404, detail="User with this email does not exist."
        )

    return user
