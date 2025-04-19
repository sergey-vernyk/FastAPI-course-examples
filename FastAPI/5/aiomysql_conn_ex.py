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


async def get_connection() -> aiomysql.Connection:
    """Отримання even loop та та отримання з'єднання до БД."""
    # поточний event loop можна не передавати як параметр до "aiomysql.connect"
    # в версії Python 3.10+
    loop = asyncio.get_event_loop()
    connection = await aiomysql.connect(**MYSQL_CONNECTION_DATA, loop=loop)
    return connection


async def shutdown() -> None:
    """Закриття з'єднання з БД після завершення програми."""
    connection = await get_connection()
    connection.close()


app = FastAPI(title="DB Async aiomysql Connection", on_shutdown=(shutdown,))


@app.post("/users/{user_name}/{user_email}")
async def create_user(user_name: str, email: str) -> dict[str, str]:
    """Створення користувача в БД з переданими іменем `user_name` та `email`."""
    connection = await get_connection()

    # створюємо курсор із з'єднання
    async with connection.cursor() as cur:
        await cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        existing_user = await cur.fetchone()

    if existing_user is not None:
        raise HTTPException(
            status_code=400, detail="User with this name already exists."
        )

    # додаємо нового користувача
    async with connection.cursor() as cur:
        await cur.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s);", (user_name, email)
        )
        await connection.commit()

    return {"user_name": user_name}


@app.get("/users/")
async def read_users() -> dict[str, Any]:
    """Отримання всіх користувачів із БД."""
    connection = await get_connection()

    # створюємо курсор із з'єднання і отримуємо всіх користувачів
    async with connection.cursor() as cur:
        await cur.execute("SELECT * FROM users;")

    users = await cur.fetchall()

    return {"users": users}


@app.get("/users/{email}")
async def read_user(email: str) -> Any:
    """Отримання всіх користувачів із БД."""
    connection = await get_connection()

    # створюємо курсор із з'єднання і отримуємо користувача по email
    async with connection.cursor() as cur:
        await cur.execute("SELECT * FROM users WHERE email=%s;", (email,))

    user = await cur.fetchone()
    if user is None:
        raise HTTPException(
            status_code=404, detail="User with this email does not exist."
        )

    return user
