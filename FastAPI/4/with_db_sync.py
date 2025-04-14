import json
import logging
import time
from typing import Sequence

import requests
from fastapi import FastAPI, HTTPException
from sqlalchemy import (
    Column,
    Integer,
    MetaData,
    Select,
    String,
    Table,
)
from sqlalchemy.engine import create_engine
from sqlalchemy.engine.row import RowMapping
from sqlalchemy.orm import Session

# pylint: disable=logging-fstring-interpolation

logging.basicConfig(
    style="{",
    level=logging.INFO,
    handlers=(logging.StreamHandler(),),
    datefmt="%Y-%m-%d %H:%M:%S",
    format="[{levelname} - {asctime}] - {name} - {message}",
)
logger = logging.getLogger(__name__)


DATABASE_URL = "sqlite:///./test_sync.db"

engine = create_engine(DATABASE_URL)
sync_session = Session(engine, expire_on_commit=False)
metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(30)),
    Column("email", String(50)),
)


def simulate_io_delay():
    """Симуляція затримки доступу до стороннього API."""
    start = time.perf_counter()
    logger.info("Start API request.")

    response = requests.get("https://httpbin.org/delay/3", timeout=6)

    end = time.perf_counter()
    logger.info(f"End API request in: {end - start:.5f} seconds.")
    return response.json()


def get_users_from_db(query: Select, session: Session) -> Sequence[RowMapping]:
    """Отримання всіх користувачів із БД."""
    start = time.perf_counter()
    logger.info("Start DB query.")

    cursor = session.execute(query)
    all_users = cursor.mappings().all()

    end = time.perf_counter()
    logger.info(f"End DB query in {end - start:.5f} seconds.")
    write_users_to_file(all_users)
    return all_users


def write_users_to_file(users: Sequence[RowMapping]) -> None:
    """Запис даних користувачів в текстовий файл."""
    start = time.perf_counter()
    logger.info("Start writing users to file.")

    with open("users_sync.txt", "w", encoding="utf-8") as fp:
        for user in users:
            # формат: "1. Jack (example@example.com)"
            fp.write(f"{user['id']}. {user['name']} ({user['email']})\n")

    end = time.perf_counter()
    logger.info(f"End writing users to file in: {end - start:.5f} seconds.")


def startup() -> None:
    """Створення таблиць в БД при старті програми."""
    with engine.connect() as connection:
        metadata.create_all(engine)
        connection.begin()


def shutdown() -> None:
    """Закриття з'єднання з БД після завершення програми."""
    engine.dispose()


app = FastAPI(on_startup=[startup], on_shutdown=[shutdown], title="DB Sync")


@app.post("/users/{user_name}/{user_email}")
def create_user(user_name: str, email: str):
    """Створення користувача в БД з переданими іменем `user_name`."""
    query = users.select().where(users.c.name == user_name)
    cursor = sync_session.execute(query)
    existing_user = cursor.fetchone()

    if existing_user is not None:
        raise HTTPException(
            status_code=400, detail="User with this name already exists"
        )

    query = users.insert().values(name=user_name, email=email)

    sync_session.execute(query)
    sync_session.commit()

    return {"user_name": user_name}


@app.get("/users/")
def read_users():
    """Отримання всіх користувачів із БД."""
    start = time.perf_counter()
    query = users.select()

    # запуск задач для доступу до стороннього API, отримання користувачів із БД
    # та запис отриманих користувачів в файл
    api_result = simulate_io_delay()
    all_users = get_users_from_db(query, sync_session)

    # отримання результату із стороннього API
    print(f"Data from API: {json.dumps(api_result, indent=2)}")

    logger.info(f"Затрачено часу: {time.perf_counter() - start:.2f} секунд.")
    return {"users": all_users}
