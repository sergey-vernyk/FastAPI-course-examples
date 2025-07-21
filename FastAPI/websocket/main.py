"""
Перевірити роботу WebSocket можна і локально.
Достатньо відкрити або різні браузери, або різні вкладки в браузері
і туди скопіювати повністю посилання, яке ви можете отримати через ендпоінт "/register/{name}"
як ми робили на уроці. І далі вже можна переписуватись з однієї вкладки до іншої.

Для того, щоб відправити особисте повідомлення то треба скопіювати ім'я користувача, якому
хочете відправити повідомлення і написати наступне у вікні для повідомлення:

name :: message

Де name - ім'я користувача
message - ваше повідомлення
:: - просто як розділювач між іменем та самим повідомленням

"""

# pip install websockets
import pathlib
import secrets
import sqlite3

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Path,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.templating import _TemplateResponse

module_path = pathlib.Path(__file__).parent

# вказуємо папку з шаблоном для чату
templates = Jinja2Templates(directory=module_path / "templates")

CHAT_DB_USERS = "chat.db"
GLOBAL_URL = "127.0.0.1:8000"


def check_token(token: str):
    """
    Перевірка токена для доступу до чату.
    Якщо токена не існує в БД, то повертається `None`.
    """
    with sqlite3.connect(CHAT_DB_USERS) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("SELECT token FROM users WHERE token = ?", (token,))
        token_db = cursor.fetchone()
        if token_db is not None:
            return token_db["token"]

        return None


def create_tables() -> None:
    """Створення таблиць в БД при старті програми."""
    with sqlite3.connect(CHAT_DB_USERS) as connection:
        cursor: sqlite3.Cursor = connection.cursor()
        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS users (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    name      VARCHAR(30) NOT NULL,
                    token     VARCHAR(32) UNIQUE NOT NULL
                );
            """
        )
        connection.commit()


app = FastAPI(title="WebSocket Global Chat", on_startup=(create_tables,))


class WebsocketConnectionManager:
    """Менеджер роботи з WebSocket."""

    def __init__(self) -> None:
        """Ініціалізація структури для зберігання з'єднань."""
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, name: str, token: str) -> None:
        """Приєднання до websocket та оповіщення всіх про це."""
        await websocket.accept()
        await self.broadcast(f"{name.title()} is online.")
        self.active_connections[token] = websocket

    def disconnect(self, token: str) -> None:
        """Від'єднання від websocket та видалення із контейнера об'єкта з'єднання."""
        self.active_connections.pop(token, None)

    async def send_personal_message(self, message: str, token: str) -> None:
        """Відправлення приватного повідомлення на одне відкрите з'єднання."""
        websocket = self.active_connections.get(token)
        if websocket:
            await websocket.send_text(message)

    async def broadcast(self, message: str, exclude: set[str] | None = None) -> None:
        """
        Відправлення загальнодоступного повідомлення на всі відкриті з'єднання,
        окрім з'єднань з `exclude`.
        """
        if exclude is None:
            exclude = set()

        for connection in (
            conn for conn in self.active_connections.values() if conn not in exclude
        ):
            await connection.send_text(message)


manager = WebsocketConnectionManager()


@app.post(
    "/register/{name}",
    status_code=status.HTTP_201_CREATED,
    response_model=None,
    operation_id="register-user",
    summary="Used for user registration to access the chat.",
    include_in_schema=True,
)
async def register(name: str = Path(max_length=30, min_length=2)):
    """Реєстрація користувача в системі для отримання доступу до чату."""
    token = secrets.token_urlsafe(32)[:32]
    with sqlite3.connect(CHAT_DB_USERS) as connection:
        connection.row_factory = sqlite3.Row
        cursor: sqlite3.Cursor = connection.cursor()
        cursor.execute(
            "SELECT 1 FROM users WHERE name = ?",
            (name,),
        )

        db_user = cursor.fetchone()
        if db_user is not None:
            raise HTTPException(400, "User exists.")

        cursor.execute(
            "INSERT INTO users (name, token) VALUES (?, ?)",
            (name, token),
        )
        connection.commit()
        cursor.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,))
        user = cursor.fetchone()

    return {"success": {"user": user, "url": f"{GLOBAL_URL}/chat/{name}/{token}"}}


@app.get(
    "/chat/{name}/{token}",
    response_model=None,
    status_code=status.HTTP_200_OK,
    operation_id="chat-page",
    description="Page for chat with Websocket.",
    include_in_schema=False,
)
async def chat_page(
    request: Request,
    token: str = Depends(check_token),
    name: str = Path(
        max_length=15,
        min_length=2,
        description="User name for chat",
    ),
) -> _TemplateResponse:
    """
    Сторінка чату з використанням WebSocket.
    Якщо токен не існує в БД, користувач не матиме доступу до чату.
    """
    if token is None:
        return HTMLResponse(
            content="<h1>403 Forbidden</h1>", status_code=status.HTTP_403_FORBIDDEN
        )

    return templates.TemplateResponse(
        request,
        name="chat.html",
        context={"token": token, "name": name, "ws_base_url": GLOBAL_URL},
    )


@app.websocket("/ws/{name}/{token}")
async def handle_chat(websocket: WebSocket, name: str, token: str) -> None:
    """Обробка з'єднання, приймання та передачі повідомлення."""
    # встановлення з'єднання
    await manager.connect(websocket, name, token)
    try:
        while True:
            # отримаємо повідомлення в форматі json (python словник)
            data = await websocket.receive_json()
            # якщо є адресат, то це повідомлення приватне
            if data.get("to") is not None:
                with sqlite3.connect(CHAT_DB_USERS) as connection:
                    connection.row_factory = sqlite3.Row
                    cursor = connection.cursor()
                    cursor.execute(
                        "SELECT token FROM users WHERE name = ?;", (data["to"],)
                    )
                    user_token = cursor.fetchone()
                    # якщо токен юзера не знайдено в БД
                    # або юзера немає в активних з'єднаннях
                    # вважаємо його як офлайн
                    if (
                        user_token is None
                        or user_token["token"] not in manager.active_connections
                    ):
                        await manager.send_personal_message(
                            f"User {data['to']} is not online.", token
                        )
                    else:
                        await manager.send_personal_message(
                            f"{name} >>> {data['message']}", user_token["token"]
                        )
                        await manager.send_personal_message(
                            f"You >>> {data['message']}", token
                        )
            else:
                # якщо немає адресата, то це повідомлення для всіх
                await manager.broadcast(
                    f"{name} >>> {data['message']}", exclude={token}
                )
    # після закриття вкладки буде викликаний цей виняток
    # клієнта буде видалено із з'єднань
    # і всі інші учасники чату отримають повідомлення про виходу із чату того учасника
    except WebSocketDisconnect:
        manager.disconnect(token)
        await manager.broadcast(f"{name} left the chat.")
