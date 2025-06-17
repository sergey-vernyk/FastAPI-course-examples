import base64

import aiosqlite
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field, SecretStr

SQLITE_DB_NAME = "mydb.db"

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


app = FastAPI(on_startup=(create_tables,), docs_url="/docs", redoc_url="/redoc")


class UserCreate(BaseModel):
    """Модель користувача для створення."""

    name: str = Field(
        description="User name", min_length=3, examples=["Bob", "Jack", "Benjamin"]
    )
    email: EmailStr = Field(description="User email", examples=["john@exampl.com"])
    password: SecretStr


class UserShow(UserCreate):
    """Модель користувача для відображення."""

    id: int = Field(description="User identification value", gt=0)
    is_active: bool = Field(
        default=False, description="User active status in the system."
    )


class Token(BaseModel):
    """Модель токена доступу."""

    token_type: str = Field(description="Type of the token.", examples=["bearer"])
    access_token: str = Field(
        description="Token value", examples=["Ym9iQGV4YW1wbGUuY29tLUJvYg=="]
    )


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


@app.get(
    "/users/me",
    status_code=status.HTTP_200_OK,
    response_model=UserShow,
    tags=["users"],
    summary="Get current active authenticated user",
    description="Endpoint used for getting inf about current active authenticated user",
    responses={
        200: {"description": "Success. User info returned."},
        401: {"description": "Data for authentication is invalid"},
        400: {"description": "User is not active"},
    },
    operation_id="get-access-token",
    include_in_schema=True,
    name="get-current-active-user",
)
async def get_user_me(
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


@app.post(
    "/token",
    response_model=Token,
    tags=["auth"],
    summary="Get access token by provided email and password",
    description="Endpoint used for auth purposes. Access token will be returned after calling it",
    responses={
        200: {"description": "Success. Token returned"},
        404: {"description": "User not found"},
        400: {"description": "Incorrect password provided"},
    },
    operation_id="get-access-token",
    include_in_schema=True,
    name="get-token",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    connection: aiosqlite.Connection = Depends(get_db),
) -> Token:
    """
    Отримання токену автентифікації для доступу до захищених ендпоінтів.
    Буде автоматично викликаний при авторизації після вводу email та пароля в SwaggerUI
    ('Authorize' кнопка справа вгорі).
    """
    async with connection.cursor() as cursor:
        await cursor.execute(
            "SELECT * FROM users WHERE email = ?;", (form_data.username,)
        )
        db_user = await cursor.fetchone()

        if db_user is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User does not exist.")

    user = UserShow(**db_user)

    if user.password.get_secret_value() != form_data.password:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Incorrect password.")

    return Token(
        access_token=base64.urlsafe_b64encode(
            f"{user.email}-{user.name}".encode("utf-8")
        ).decode("utf-8"),
        token_type="bearer",
    )


@app.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserShow,
    tags=["users"],
    summary="User registration",
    description="Endpoint used for user registration",
    responses={
        201: {"description": "Success. User data returned"},
        400: {"description": "User already exists"},
    },
    operation_id="register-user",
    include_in_schema=True,
    name="register_user",
)
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
                True,
            ),
        )

        last_inserted = await cursor.fetchone()
        await connection.commit()

    return UserShow(
        **user_data.model_dump(exclude={"is_active"}),
        id=last_inserted["id"],
        is_active=True,
    )


@app.get(
    "/users/",
    status_code=status.HTTP_200_OK,
    response_model=list[UserShow],
    tags=["users"],
    summary="Get all users with limit",
    description="Endpoint used for getting users with provided limit",
    response_description="Users info returned",
    operation_id="get-users",
    include_in_schema=True,
    name="get-users",
)
async def get_users(
    limit: int = Query(
        default=10, description="Maximum number of returned users", gt=0
    ),
    connection: aiosqlite.Connection = Depends(get_db),
) -> list[UserShow]:
    """Отримання всіх користувачів з БД враховуючи ліміт."""
    async with connection.cursor() as cursor:
        await cursor.execute("SELECT * FROM users LIMIT ?;", (limit,))
        db_users = await cursor.fetchall()

    return [UserShow(**data) for data in db_users]
