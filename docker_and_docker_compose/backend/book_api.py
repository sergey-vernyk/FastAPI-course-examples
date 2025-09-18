import os
from contextlib import asynccontextmanager

import aiomysql
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

load_dotenv(".env")

MYSQL_CONNECTION_DATA = {
    "host": os.environ.get("MYSQL_HOST"),
    "port": int(os.environ.get("MYSQL_PORT", 3306)),
    "user": os.environ.get("MYSQL_USER"),
    "password": os.environ.get("MYSQL_PASSWORD"),
    "db": os.environ.get("MYSQL_DB"),
}


async def get_mysql_connection() -> aiomysql.Connection:
    """Створення та повернення з'єднання."""
    return await aiomysql.connect(**MYSQL_CONNECTION_DATA)


class Book(BaseModel):
    """Базова модель книги."""

    title: str
    author: str
    year: int


class BookInfo(Book):
    """Модель книги для відображення."""

    id: int
    title: str
    author: str
    year: int


class BookUpdate(BaseModel):
    """Модель книги для оновлення."""

    title: str | None = None
    author: str | None = None
    year: int | None = None


@asynccontextmanager
async def create_tables(_: FastAPI):
    """
    Створення таблиць в БД при старті програми та закриття з'єднання з БД після завершення.
    """
    async with aiomysql.connect(**MYSQL_CONNECTION_DATA) as connection:
        cursor: aiomysql.Cursor = await connection.cursor()
        await cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT,
                name VARCHAR(50),
                email VARCHAR(50),
                PRIMARY KEY(id)
            );
            """
        )
        await cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS books (
                id INT AUTO_INCREMENT,
                title VARCHAR(50),
                author VARCHAR(50),
                year INTEGER,
                PRIMARY KEY(id)
            );
            """
        )
        await connection.commit()

    yield


app = FastAPI(title="Book API", lifespan=create_tables)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/books/")
async def create_book(book: Book) -> BookInfo:
    """Створення книги."""
    connection = await get_mysql_connection()

    try:
        async with connection.cursor() as cursor:
            # перевіряємо наявність в БД книги з переданою назвою
            await cursor.execute("SELECT 1 FROM books WHERE title=%s;", (book.title,))
            db_book = await cursor.fetchone()

            if db_book is not None:
                raise HTTPException(400, "Book is already exists.")

            # створюємо книгу, якщо її не знайшлось в БД
            await cursor.execute(
                "INSERT INTO books (title, author, year) VALUES (%s, %s, %s);",
                (
                    book.title,
                    book.author,
                    book.year,
                ),
            )
            await connection.commit()
            # дістаємо останній ID книги, яку додали (працює лише в MySQL)
            await cursor.execute("SELECT LAST_INSERT_ID();")
            user_id = await cursor.fetchone()
    except aiomysql.Error as e:
        raise e
    finally:
        # в будь-якому випадку закриваємо з'єднання
        await connection.ensure_closed()

    return BookInfo(**book.model_dump(), id=user_id[0])


@app.get("/books/")
async def get_books(
    limit: int = Query(default=100, description="Кількість книг для отримання."),
) -> list[BookInfo]:
    """Отримання інформації про всіх користувачів."""
    connection = await get_mysql_connection()

    try:
        # aiomysql.DictCursor курсор, який повертає дані з БД в вигляді словника
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM books LIMIT %s;", (limit,))
            db_books = await cursor.fetchall()
    except aiomysql.Error as e:
        raise e
    finally:
        # в будь-якому випадку закриваємо з'єднання
        await connection.ensure_closed()

    return [BookInfo(**data) for data in db_books]


@app.get("/books/{book_id}")
async def get_book(book_id: int) -> BookInfo:
    """Отримання інформації про всіх користувачів."""
    connection = await get_mysql_connection()

    try:
        # aiomysql.DictCursor курсор, який повертає дані з БД в вигляді словника
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM books WHERE id=%s", book_id)
            db_book = await cursor.fetchone()

            if db_book is None:
                raise HTTPException(404, "Book does not exist.")

    except aiomysql.Error as e:
        raise e
    finally:
        # в будь-якому випадку закриваємо з'єднання
        await connection.ensure_closed()

    return BookInfo(**db_book)


@app.put("/books/{book_id}")
async def update_book(book_id: int, update_data: BookUpdate) -> BookInfo:
    """Оновлення даних книги по `book_id`."""
    connection = await get_mysql_connection()

    try:
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            # перевіряємо наявність в БД книги з переданим ID
            await cursor.execute("SELECT * FROM books WHERE id=%s;", (book_id,))
            db_book = await cursor.fetchone()

            if db_book is None:
                raise HTTPException(404, "Book does not exist.")

            # оновлюємо дані книги
            await cursor.execute(
                "UPDATE books SET title=%s, author=%s, year=%s WHERE id=%s",
                (
                    update_data.title,
                    update_data.author,
                    update_data.year,
                    book_id,
                ),
            )
            await connection.commit()
    except aiomysql.Error as e:
        raise e
    finally:
        # в будь-якому випадку закриваємо з'єднання
        await connection.ensure_closed()

    return BookInfo(**update_data.model_dump(), id=db_book["id"])


@app.delete("/books/{book_id}", response_class=JSONResponse, status_code=204)
async def delete_book(book_id: int) -> None:
    """Видалення книги по `book_id`."""
    connection = await get_mysql_connection()

    try:
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            # перевіряємо наявність в БД книги з переданим ID
            await cursor.execute("SELECT 1 FROM books WHERE id=%s;", (book_id,))
            db_book = await cursor.fetchone()

            if db_book is None:
                raise HTTPException(404, "Book does not exist.")

            # видаляємо книгу
            await cursor.execute("DELETE FROM books WHERE id=%s", (book_id,))
            await connection.commit()
    except aiomysql.Error as e:
        raise e
    finally:
        # в будь-якому випадку закриваємо з'єднання
        await connection.ensure_closed()


@app.patch("/books/{book_id}")
async def update_book_partial(book_id: int, update_data: BookUpdate) -> BookInfo:
    """Часткове оновлення даних книги по `book_id`."""
    connection = await get_mysql_connection()

    try:
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            # перевіряємо наявність в БД книги з переданим ID
            await cursor.execute("SELECT * FROM books WHERE id=%s;", (book_id,))
            db_book: dict = await cursor.fetchone()

            if db_book is None:
                raise HTTPException(404, "Book does not exist.")

            # залишаємо тільки ті дані, які треба оновити
            updated_item = update_data.model_dump(exclude_unset=True)
            # формуємо строку із назвами полів для оновлення у вигляді (title=%s, author=%s)
            set_clauses = ",".join(f"{field}=%s" for field in updated_item.keys())
            # значення для оновлення
            values = list(updated_item.values())

            # оновлюємо дані книги
            await cursor.execute(
                f"UPDATE books SET {set_clauses} WHERE id=%s;",
                values + [book_id],
            )
            await connection.commit()
    except aiomysql.Error as e:
        raise e
    finally:
        # в будь-якому випадку закриваємо з'єднання
        await connection.ensure_closed()

    # оновлюємо дані книги для відповіді
    db_book.update(**updated_item)
    return BookInfo(**db_book)
