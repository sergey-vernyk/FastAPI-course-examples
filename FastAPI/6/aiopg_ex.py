import os

import aiopg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

load_dotenv(os.path.abspath(f"{os.path.pardir}/.env"))

# завантажуємо конфіденційні дані доступу до бази даних PostgreSQL із файлу .env
POSTGRES_CONNECTION_DATA = {
    "host": os.environ.get("POSTGRES_HOST"),
    "port": int(os.environ.get("POSTGRES_PORT", 5432)),
    "user": os.environ.get("POSTGRES_USER"),
    "password": os.environ.get("POSTGRES_PASSWORD"),
    "db": os.environ.get("POSTGRES_DB"),
}


DSN = (
    f"dbname={POSTGRES_CONNECTION_DATA['db']} "
    f"user={POSTGRES_CONNECTION_DATA['user']} "
    f"password={POSTGRES_CONNECTION_DATA['password']} "
    f"host={POSTGRES_CONNECTION_DATA['host']} "
    f"port={POSTGRES_CONNECTION_DATA['port']}"
)


async def get_pool() -> aiopg.Pool:
    """Створення пулу з'єднань до БД."""
    pool = await aiopg.create_pool(DSN)
    return pool


async def shutdown() -> None:
    """Закриття пулу з'єднань з БД після завершення програми."""
    pool = await get_pool()
    pool.close()
    await pool.wait_closed()


app = FastAPI(title="DB Async aiopg", on_shutdown=(shutdown,))


@app.post("/users/{user_name}/{user_email}")
async def create_user(user_name: str, user_email: str):
    """Створення користувача в БД з переданими іменем `user_name` та `email`."""
    pool = await get_pool()

    try:
        # отримуємо з'єднання з пулу
        async with pool.acquire() as connection:
            async with connection.cursor() as cur:
                await cur.execute("SELECT * FROM users WHERE email=%s", (user_email,))
                existing_user = await cur.fetchone()

                if existing_user is not None:
                    raise HTTPException(
                        status_code=400, detail="User with this email already exists."
                    )

        # додаємо нового користувача
        async with pool.acquire() as connection:
            async with connection.cursor() as cur:
                await cur.execute(
                    "INSERT INTO users (name, email) VALUES (%s, %s);",
                    (user_name, user_email),
                )
                # не потрібно при використанні цієї бібліотеки
                # await connection.commit()
    finally:
        # пул з'єднань буде автоматично закритий
        pool.close()
        await pool.wait_closed()

    return {"user_name": user_name}


@app.get("/users/")
async def read_users():
    """Отримання всіх користувачів із БД."""
    pool = await get_pool()

    # отримуємо з'єднання з пулу і отримуємо всіх користувачів
    async with pool.acquire() as connection:
        async with connection.cursor() as cur:
            await cur.execute("SELECT * FROM users;")
            users = await cur.fetchall()

    # закриваємо пул з'єднань
    pool.close()
    await pool.wait_closed()

    return {"users": users}


@app.get("/users/{email}")
async def read_user(email: str):
    """Отримання всіх користувачів із БД."""
    pool = await get_pool()

    # отримуємо з'єднання з пулу і отримуємо всіх користувачів
    async with pool.acquire() as connection:
        async with connection.cursor() as cur:
            await cur.execute("SELECT * FROM users WHERE email=%s;", (email,))

            user = await cur.fetchone()
            if user is None:
                raise HTTPException(
                    status_code=404, detail="User with this email does not exist."
                )

    # закриваємо пул з'єднань
    pool.close()
    await pool.wait_closed()

    return user
