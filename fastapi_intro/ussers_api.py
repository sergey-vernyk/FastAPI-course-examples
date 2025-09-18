import sqlite3
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

DB_NAME = "my_db.db"


class BaseUser(BaseModel):
    """Базова модель для створення користувача."""

    first_name: str
    last_name: str
    email: str


class CreateUser(BaseUser):
    """Модель для створення користувача."""

    first_name: str
    last_name: str
    email: str


class UserInfo(BaseUser):
    """Модель для отримання користувача."""

    id: int


@asynccontextmanager
async def create_tables(_: FastAPI):
    """Створення таблиць в БД при старті програми."""
    try:
        with sqlite3.connect(DB_NAME, check_same_thread=True) as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user (
                    id INTEGER PRIMARY KEY,
                    first_name VARCHAR(50),
                    last_name VARCHAR(50),
                    email VARCHAR(50)
                );
                """
            )
            connection.commit()
    except sqlite3.Error as e:
        raise e

    yield


app = FastAPI(lifespan=create_tables)


@app.post("/users/", status_code=201, response_model=UserInfo, tags=["users"])
def create_user(user: CreateUser) -> UserInfo:
    """Створення користувача."""
    with sqlite3.connect(DB_NAME, check_same_thread=True) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO user (first_name, last_name, email) VALUES (?, ?, ?) RETURNING *;",
            (*user.model_dump().values(),),
        )
        rows = cur.fetchone()
        conn.commit()

    user_fields = ("id", "first_name", "last_name", "email")
    return UserInfo(**dict(zip(user_fields, rows)))


@app.get("/users/{user_id}", status_code=200, response_model=UserInfo, tags=["users"])
def get_user(user_id: int) -> UserInfo:
    """Отримання користувача по ID."""
    with sqlite3.connect(DB_NAME, check_same_thread=True) as conn:
        cur = conn.cursor()
        # перевіряємо, чи користувач існує
        cur.execute(
            "SELECT id, first_name, last_name, email FROM user WHERE id = ?;",
            (user_id,),
        )
    raw = cur.fetchone()
    if raw is None:
        raise HTTPException(status_code=404, detail="User not found.")

    user_fields = ("id", "first_name", "last_name", "email")
    user_info = dict(zip(user_fields, raw))
    user = UserInfo(**user_info)
    return user


@app.get("/users/", status_code=200, response_model=list[UserInfo], tags=["users"])
def get_users(
    skip: int = Query(default=0), limit: int = Query(default=100)
) -> list[UserInfo]:
    """Отримання користувачів."""
    with sqlite3.connect(DB_NAME, check_same_thread=True) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, first_name, last_name, email FROM user LIMIT :limit OFFSET :skip;",
            (limit, skip),
        )
    rows = cur.fetchall()
    user_fields = ("id", "first_name", "last_name", "email")
    users = [UserInfo(**dict(zip(user_fields, row))) for row in rows]
    return users


@app.put("/users/{user_id}", status_code=200, response_model=UserInfo, tags=["users"])
def update_user(user_id: int, data_to_update: BaseUser) -> UserInfo:
    """Оновлення користувача по ID."""
    with sqlite3.connect(DB_NAME, check_same_thread=True) as conn:
        cursor = conn.cursor()
        # перевіряємо, чи користувач існує
        cursor.execute(
            "SELECT 1 FROM user WHERE id = ?",
            (user_id,),
        )
        raw = cursor.fetchone()
        if raw is None:
            raise HTTPException(status_code=404, detail="User not found.")

        # оновлюємо дані користувача передані в тілі запиту
        cursor = cursor.execute(
            "UPDATE user SET first_name = ?, last_name = ?, email = ? WHERE id = ? RETURNING *;",
            (*data_to_update.model_dump().values(), user_id),
        )
        raw = cursor.fetchone()
        conn.commit()

    user_fields = ("id", "first_name", "last_name", "email")
    user_info = dict(zip(user_fields, raw))
    user = UserInfo(**user_info)
    return user


@app.delete("/users/{user_id}", status_code=204, tags=["users"])
def delete_user(user_id: int) -> None:
    """Видалення користувача по ID."""
    with sqlite3.connect(DB_NAME, check_same_thread=True) as conn:
        cur = conn.cursor()
        # перевіряємо, чи користувач існує
        cur.execute(
            "SELECT 1 FROM user WHERE id = ?",
            (user_id,),
        )
        raw = cur.fetchone()
        if raw is None:
            raise HTTPException(status_code=404, detail="User not found.")

        # видаляємо користувача
        cur = cur.execute(
            "DELETE FROM user WHERE id = ?",
            (user_id,),
        )
        conn.commit()
