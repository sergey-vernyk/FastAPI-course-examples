import json

import aiosqlite
from fastapi import FastAPI, Header, HTTPException, Path, Query, Request

DATABASE_URL = "./mydb.db"

# pip install aiosqlite


async def init_database() -> None:
    """Створення таблиць в БД при запуску сервера."""
    async with aiosqlite.connect(DATABASE_URL) as connection:
        cursor = await connection.cursor()
        await cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name VARCHAR(50) NOT NULL,
                phone VARCHAR(50) NOT NULL,
                email VARCHAR(50) NOT NULL,
                age INTEGER NOT NULL
        );
        """
        )
        await connection.commit()


app = FastAPI(title="Users API", on_startup=(init_database,))


# http://127.0.0.1:8000/users/?skip=5&limit=20.
# [
# {"id":6,"name":"Erik Valentine","phone":"+1-789-012-3456","email":"ydelgado@yahoo.com","age":22},
# {"id":7,"name":"Donald Hopkins","phone":"+1-890-123-4567","email":"mcintyrechristopher@hotmail.com","age":45}
# ...
# ]
@app.get("/users/")
async def get_users(
    request: Request,
    skip: int = Query(
        0,
        title="Пропустити",
        description="Кількість записів для пропуску.",
    ),
    limit: int = Query(
        100,
        title="Ліміт",
        description="Максимальна кількість записів для видачі.",
    ),
):
    """Отримання всіх користувачів в діапазоні `skip` та `limit`."""
    print(f"Параметри запиту: {request.query_params}")

    async with aiosqlite.connect(DATABASE_URL) as connection:
        # повертає записи з БД у вигляді словника
        connection.row_factory = aiosqlite.Row
        cursor = await connection.cursor()
        await cursor.execute("SELECT * FROM users LIMIT ? OFFSET ?;", (limit, skip))
        users = await cursor.fetchall()

    return users


# http://127.0.0.1:8000/users/search/?name=John&age=37
# [{"id":5,"name":"John Hill","phone":"+1-678-901-2345","email":"robertsontammy@hotmail.com","age":37}]
@app.get("/users/search/")
async def search_users(
    request: Request,
    name: str = Query(
        ...,
        title="Пошук по імені",
        description="Запит для пошуку користувачів по імені.",
    ),
    age: int | None = Query(
        None,
        title="Пошук по віку",
        lt=101,
        gt=29,
        description="Запит для пошуку користувачів по віку.",
    ),
):
    """Пошук користувачів по імені та віку."""
    print(f"Параметри запиту: {request.query_params}")

    async with aiosqlite.connect(DATABASE_URL) as connection:
        # повертає записи з БД у вигляді словника
        connection.row_factory = aiosqlite.Row
        cursor = await connection.cursor()
        if age is not None:
            await cursor.execute(
                "SELECT * FROM users WHERE name LIKE ? AND age = ?;", (f"%{name}%", age)
            )
        else:
            await cursor.execute(
                "SELECT * FROM users WHERE name LIKE ?", (f"%{name}%",)
            )
        users = await cursor.fetchall()

    return users


# http://127.0.0.1:8000/users/52
# {"id":52,"name":"Jared Dawson","phone":"+1-345-678-9012","email":"huertajames@stanley.com","age":31}
@app.get("/users/{user_id}")
async def get_user(
    request: Request,
    user_id: int = Path(gt=0, description="ID користувача."),
):
    """Отримання користувача по ID."""
    print(f"Параметри шляху: {request.path_params}")

    async with aiosqlite.connect(DATABASE_URL) as connection:
        # повертає записи з БД у вигляді словника
        connection.row_factory = aiosqlite.Row
        cursor = await connection.cursor()
        await cursor.execute("SELECT * FROM users WHERE id = ?;", (user_id,))

        user = await cursor.fetchone()
        if user is None:
            raise HTTPException(404, "User does not exist.")

    return user
