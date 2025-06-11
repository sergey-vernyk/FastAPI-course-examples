import base64

import aiosqlite
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import (
    HTTPBasic,
    HTTPBasicCredentials,
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)
from pydantic import BaseModel, EmailStr, SecretStr

# pip install python-multipart

SQLITE_DB_NAME = "mydb.db"

security = HTTPBasic()
# схема автентифікації/авторизації за допомогою токена
# URL ендпоінта для отримання токена - http://127.0.0.1:8000/token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_db():
    """Створення там повернення з'єднання з БД."""
    async with aiosqlite.connect(SQLITE_DB_NAME) as connection:
        connection.row_factory = aiosqlite.Row
        yield connection

        await connection.close()


async def create_tables() -> None:
    """Створення таблиць в БД при старті програми та автоматичне закриття з'єднання після завершення."""
    async with aiosqlite.connect(SQLITE_DB_NAME) as connection:
        cursor: aiosqlite.Cursor = await connection.cursor()
        await cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS users (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    name      VARCHAR(30) NOT NULL,
                    email     VARCHAR(50) NOT NULL,
                    password  VARCHAR(30) NOT NULL,
                    is_active BOOLEAN NOT NULL CHECK (is_active IN (0, 1))
                );
            """
        )
        await connection.commit()
        await connection.close()


app = FastAPI(on_startup=(create_tables,))


class UserCreate(BaseModel):
    """Модель користувача для створення."""

    name: str
    email: EmailStr
    password: SecretStr
    is_active: bool = False


class UserShow(UserCreate):
    """Модель користувача для відображення."""

    id: int


class Token(BaseModel):
    """Модель токена доступу."""

    token_type: str
    access_token: str


async def decode_token(token: str):
    """
    Декодування токену доступу отриманого з заголовку Authorization.
    Приклад: Authorization: Bearer am9obi5kb2VAZXhhbXBsZS5jb20tSm9obiBEb2U=
    """
    try:
        # дістаємо з закодованого токену email користувача
        # email-name.split("-")[0] --> email
        decoded_user_email = (
            base64.urlsafe_b64decode(token).split(b"-")[0].decode("utf-8")
        )
    except (UnicodeDecodeError, ValueError):
        return None

    return decoded_user_email


#  'http://127.0.0.1:8000/users/me' \
#  -H 'accept: application/json' \
#  -H 'Authorization: Bearer am9obi5kb2VAZXhhbXBsZS5jb20tSm9obiBEb2U='
@app.get("/users/me/token", status_code=status.HTTP_200_OK, response_model=UserShow)
async def get_user_me_token(
    token: str = Depends(oauth2_scheme),
    connection: aiosqlite.Connection = Depends(get_db),
) -> UserShow:
    """Отримання даних про поточного автентифікованого користувача."""
    decoded_email = await decode_token(token)

    async with connection.cursor() as cursor:
        await cursor.execute("SELECT * FROM users WHERE email = ?;", (decoded_email,))
        db_user = await cursor.fetchone()

        # якщо декодування токену не вдале
        # і не вдалось отримати користувача із декодованого токену
        if db_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                # заголовок показує тип автентифікації - Bearer токен
                headers={"WWW-Authenticate": "Bearer"},
            )

    decoded_user = UserShow(**db_user)

    if not decoded_user.is_active:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "User is not active.")

    return decoded_user


# curl -X 'GET' \
#  'http://127.0.0.1:8000/users/me/basic' \
#  -H 'accept: application/json' \
#  -u bob@example.com:bob-password
@app.get("/users/me/basic", status_code=status.HTTP_200_OK, response_model=UserShow)
async def get_user_me_basic(
    credentials: HTTPBasicCredentials = Depends(security),
    connection: aiosqlite.Connection = Depends(get_db),
) -> UserShow:
    """
    Отримання даних про поточного автентифікованого користувача
    з використанням базової автентифікації.
    Токен не повертається, проте також закодоване значення (email:password)
    передається в Authorization заголовку.
    """
    async with connection.cursor() as cursor:
        await cursor.execute(
            "SELECT * FROM users WHERE email = ? AND password = ?;",
            (credentials.username, credentials.password),
        )
        db_user = await cursor.fetchone()

        # якщо не вдалось отримати користувача із декодованих переданих даних
        if db_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                # заголовок показує тип автентифікації - базова
                headers={"WWW-Authenticate": "Basic"},
            )

    decoded_user = UserShow(**db_user)

    if not decoded_user.is_active:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "User is not active.")

    return decoded_user


# curl -X 'POST' \
#  'http://127.0.0.1:8000/token' \
#  -H 'accept: application/json' \
#  -H 'Content-Type: application/x-www-form-urlencoded' \
#  -d 'grant_type=password&username=john.doe@example.com&password=super-password&scope=&client_id=string&client_secret=string'
@app.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    connection: aiosqlite.Connection = Depends(get_db),
) -> Token:
    """
    Отримання токену автентифікації для доступу до захищених ендпоінтів.
    Буде автоматично викликаний при авторизації після вводу email та пароля в SwaggerUI
    ('Authorize' кнопка справа вгорі)ю
    """
    async with connection.cursor() as cursor:
        await cursor.execute(
            "SELECT * FROM users WHERE email = ?;", (form_data.username,)
        )
        db_user = await cursor.fetchone()

        if db_user is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User does not exist.")

    user = UserShow(**db_user)

    # перевірка переданого паролю із форми і збереженого паролю в БД для цього користувача
    # необхідно явно порівнювати пароль збережений в БД, а не його захищену версію (*****)
    if user.password.get_secret_value() != form_data.password:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Incorrect password.")

    # кодування токена доступу в base64 кодування ([a-z], [A-Z], [0-9] -, _)
    # безпечне для передавання в URL
    return Token(
        access_token=base64.urlsafe_b64encode(
            f"{user.email}-{user.name}".encode("utf-8")
        ).decode("utf-8"),
        token_type="bearer",
    )


# curl -X 'POST' \                                                                                                                                                      130 ↵
# 'http://127.0.0.1:8000/register' \
#  -H 'accept: application/json' \
#  -H 'Content-Type: application/json' \
#  -d '{ "name": "Jack Smith", "email": "jack.smith@example.com", "password": "secure-password", "is_active": true}'
@app.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserShow)
async def user_registration(
    user_data: UserCreate, connection: aiosqlite.Connection = Depends(get_db)
) -> UserShow:
    """Реєстрацію користувача в базі даних."""
    async with connection.cursor() as cursor:
        await cursor.execute("SELECT 1 FROM users WHERE email = ?;", (user_data.email,))
        db_user = await cursor.fetchone()

        if db_user is not None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "User exists.")

        await cursor.execute(
            "INSERT INTO users (name, email, password, is_active) VALUES (?, ?, ?, ?) RETURNING id;",
            (
                user_data.name,
                user_data.email,
                # необхідно явно записати в БД пароль, а не *****
                user_data.password.get_secret_value(),
                user_data.is_active,
            ),
        )

        last_inserted = await cursor.fetchone()
        await connection.commit()

    return UserShow(**user_data.model_dump(), id=last_inserted["id"])


# треба розкоментувати в останню чергу тільки для перевірки цього middleware
# @app.middleware("http")
# async def authenticate_request(request: Request, call_next):
#     token = request.headers.get("Authorization")
#     if not token or not await decode_token(token):
#         return JSONResponse(
#             status_code=401, content={"detail": "Invalid or missing token."}
#         )
