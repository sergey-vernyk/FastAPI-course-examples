import base64
import logging
import sqlite3
import time
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)
from log_config import configure_logger
from middlewares import add_trace_id
from pydantic import BaseModel, EmailStr, SecretStr

SQLITE_DB_NAME = "logs.db"


def create_tables() -> None:
    """Створення таблиць в БД при старті програми."""
    with sqlite3.connect(SQLITE_DB_NAME) as connection:
        cursor: sqlite3.Cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS logs (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                trace_id  VARCHAR(36) NOT NULL,
                data      TEXT NOT NULL,
                module    VARCHAR(50) NOT NULL,
                func_name VARCHAR(50) NOT NULL,
                level     VARCHAR(10) NOT NULL,
                message   TEXT NOT NULL
            );
            """
        )
        connection.commit()


app = FastAPI(on_startup=(create_tables,))
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# створюємо логер для модуля і конфігуруємо його
logger = configure_logger(__name__)

# реєструємо наш middleware
app.middleware("http")(add_trace_id)

# можна розкоментувати тільки для перевірки, інакше працювати не буде
# так як ми не налаштовуємо HTTPS
# middleware використовується для переадресування трафіку з не захищеного на захищений протокол
# app.add_middleware(HTTPSRedirectMiddleware)


# також можна розкоментувати тільки для перевірки інакше завжди буду помилка 400
# цей middleware використовується для конфігурації дозволених хостів
# які можуть мати доступ до вашого бекенду
# curl -X POST "http://127.0.0.1:8000/register" \
# -H "accept: application/json" \
# -H "Content-Type: application/json" -H "Host: example.com" \
# -d '{"id": 1, "name": "John", "email": "john@example.com", "password": "password"}'
# app.add_middleware(
#     TrustedHostMiddleware, allowed_hosts=["example.com", "*.example.com"]
# )


# використовується для налаштування взаємодії бекенду і фронтенду
# фронтенд працює на localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class User(BaseModel):
    """Модель користувача."""

    id: int
    name: str
    email: EmailStr
    password: SecretStr


users: list[User] = []


async def decode_token(token: str):
    """
    Декодування токену доступу отриманого з заголовку Authorization.
    Приклад: Authorization: Bearer am9obi5kb2VAZXhhbXBsZS5jb20tSm9obiBEb2U=
    """
    try:
        decoded_user_email = (
            base64.urlsafe_b64decode(token).split(b"-")[0].decode("utf-8")
        )
    except (UnicodeDecodeError, ValueError):
        return None

    return decoded_user_email


# curl -X POST "http://127.0.0.1:8000/token" \
#  -H "accept: application/json" \
#  -H "Content-Type: application/x-www-form-urlencoded" \
#  -d "grant_type=password&username=john@example.com&password=password"


# am9obkBleGFtcGxlLmNvbS1Kb2hu
@app.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """
    Отримання токену автентифікації для доступу до захищених ендпоінтів.
    Буде автоматично викликаний при авторизації після вводу email та пароля в SwaggerUI
    ('Authorize' кнопка справа вгорі)
    """
    db_user = next((u for u in users if u.email == form_data.username), None)

    if db_user is None:
        # додавання логера для фіксації і зберігання подій в коді
        logger.error("User with email '%s' does not exist.", form_data.username)
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User does not exists.")

    user = User(**db_user.model_dump())
    if user.password.get_secret_value() != form_data.password:
        logger.error("Incorrect password for email '%s'", user.email)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Incorrect password.")

    logger.info("Token for email '%s' returned.", user.email)
    return {
        "access_token": base64.urlsafe_b64encode(
            f"{user.email}-{user.name}".encode("utf-8")
        ).decode("utf-8"),
        "token_type": "bearer",
    }


# curl -X GET http://127.0.0.1:8000/users/me \                                                                                                                          130 ↵
#  -H "accept: application/json" \
#  -H "Authorization: Bearer am9obkBleGFtcGxlLmNvbS1Kb2hu"
@app.get("/users/me", status_code=status.HTTP_200_OK, response_model=User)
async def get_user_me(
    token: str = Depends(oauth2_scheme),
) -> User:
    """Отримання даних про поточного автентифікованого користувача."""
    decoded_email = await decode_token(token)
    if decoded_email not in {u.email for u in users}:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = [u for u in users if u.email == decoded_email][0]
    return User(id=user.id, name=user.name, email=user.email, password=user.password)


# curl -X POST "http://127.0.0.1:8000/register" \
#  -H "accept: application/json" \
#  -H "Content-Type: application/json" \
#  -d '{"id": 1, "name": "John", "email": "john@example.com", "password": "password"}'
@app.post("/register", status_code=status.HTTP_201_CREATED, response_model=User)
async def user_registration(user_data: User) -> User:
    """Реєстрацію користувача в базі даних."""
    if user_data.email in {u.email for u in users}:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "User exists.")

    users.append(user_data)
    return User(**user_data.model_dump())


@app.get("/logs/{trace_id}", status_code=status.HTTP_200_OK)
async def get_log(trace_id: str) -> list[dict[str, Any]]:
    """Отримання логів з `trace_id`."""
    with sqlite3.Connection(SQLITE_DB_NAME) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM logs WHERE trace_id = ?", (trace_id,))
        logs = cursor.fetchone()

        if logs is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Log does not exist.")

    return logs


# краще закоментувати при перевірці іншого коду
# інакше завжди буде помилка 'Invalid or missing token'.
@app.middleware("http")
async def authenticate_request(request: Request, call_next):
    """Використовується для перевірки заголовка автентифікації при кожному запиті."""
    token = request.headers.get("Authorization")
    if not token or not await decode_token(token):
        return JSONResponse(
            status_code=401, content={"detail": "Invalid or missing token."}
        )


@app.middleware("http")
async def add_process_time_header(request: Request, call_next) -> Any:
    """Додавання часу між запитом та відповіддю в заголовок відповіді."""
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.6f}"
    return response
