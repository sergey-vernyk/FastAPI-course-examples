import aiosqlite
import bcrypt

SQLITE_DB_NAME = "mini2.db"


async def create_tables():
    async with aiosqlite.connect(SQLITE_DB_NAME) as connection:
        cursor: aiosqlite.Cursor = await connection.cursor()

        await cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS Users(
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    name         VARCHAR(30) NOT NULL,
                    email        email VARCHAR(30) NOT NULL UNIQUE,
                    password     VARCHAR(100) NOT NULL,
                    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        await cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS Posts(
                    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id                 INTEGER NOT NULL,
                    title                   VARCHAR(30) NOT NULL,
                    description             VARCHAR(300) NOT NULL,
                    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id)    REFERENCES Users(id) ON DELETE CASCADE
                );
            """
        )

        await connection.commit()
        await connection.close()


async def get_db():
    async with aiosqlite.connect(SQLITE_DB_NAME) as connection:
        connection.row_factory = aiosqlite.Row
        yield connection

        await connection.close()


def hash_password(password: str) -> str:
    bytes_password = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hash_bytes = bcrypt.hashpw(bytes_password, salt)
    return hash_bytes.decode("utf-8")


def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
