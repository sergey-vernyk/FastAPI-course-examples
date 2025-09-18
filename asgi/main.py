import json
from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any

import uvicorn

type Scope = MutableMapping[str, Any]
type Message = MutableMapping[str, Any]

# async def receive() -> Message: ...
type Receive = Callable[[], Awaitable[Message]]

# async def send(m: Message) -> None: ...
type Send = Callable[[Message], Awaitable[None]]


async def app(scope: Scope, receive: Receive, send: Send) -> None:
    """Основна програма, яка запускається за допомогою Uvicorn."""
    print("-" * 150)
    print(f"Beginning connection. Scope: {scope}", end="\n")
    print("-" * 150)

    match scope["type"]:
        case "lifespan":
            await handle_lifetime(scope, receive, send)
        case "http":
            await handle_http(scope, receive, send)
        case "websocket":
            await handle_websocket(scope, receive, send)

    print("Ending connection")


async def handle_lifetime(scope: Scope, receive: Receive, send: Send) -> None:
    """Обробник життєвого циклу додатку."""
    assert scope["type"] == "lifespan"
    print(f"Lifetime connection. Scope: {scope}", end="\n")
    print("-" * 150)

    while True:
        message: Message = await receive()
        print(f"Got message: {message}")

        if message["type"] == "lifespan.startup":
            # відправляється додатком коли він повністю запустився
            await send({"type": "lifespan.startup.complete"})
            print("Application started.")
        elif message["type"] == "lifespan.shutdown":
            # відправляється до додатку коли сервер припинив приймати з'єднання та закрив всі активні з'єднання
            await send({"type": "lifespan.shutdown.complete"})
            print("Application stopped.")
            break


async def handle_http(scope: Scope, receive: Receive, send: Send) -> None:
    """Обробник HTTP scope."""
    assert scope["type"] == "http"
    print(f"Handle http. Scope: {scope}", end="\n")
    print("-" * 150)

    if scope["path"] == "/echo" and scope["method"] == "POST":
        await echo_endpoint(scope, receive, send)
    elif scope["path"] == "/status" and scope["method"] == "GET":
        await status_endpoint(scope, receive, send)
    else:
        await error_endpoint(scope, receive, send)


# curl -X POST http://127.0.0.1:8000/echo \
# -H "Content-Type: application\json" \
# -d '{"status": "success"}'
async def echo_endpoint(scope: Scope, receive: Receive, send: Send) -> None:
    """Обробник ендпоінту для ехо запитів."""
    print(f"Echo endpoint. Scope: {scope}", end="\n")
    print("-" * 150)

    data = []
    while True:
        print("Waiting for message...")

        message: Message = await receive()
        print(f"Received message: {message}")

        # відправляється до додатку коли отримання (receive) викликається після відправки відповіді
        # або після закриття HTTP з'єднання
        if message["type"] == "http.disconnect":
            print("HTTP Disconnected.")
            return

        # перевірка, щоб тип події був request (запит)
        assert message["type"] == "http.request"

        data.append(message["body"])

        # якщо більше немає даних для отримання в тілі запиту
        if not message["more_body"]:
            break

    response_message = {
        "type": "http.response.start",
        "status": 200,
        "headers": [(b"content-type", b"application/json")],
    }
    print(f"Sending response start: {response_message}")
    print("-" * 150)
    await send(response_message)

    response_message = {
        "type": "http.response.body",
        "body": b"".join(data),
        "more_body": False,
    }
    print(f"Sending response body: {response_message}")
    print("-" * 150)
    await send(response_message)


# curl -X GET http://127.0.0.1:8000/status
async def status_endpoint(scope: Scope, receive: Receive, send: Send) -> None:
    """Обробник ендпоінту для отримання статусу."""
    print(f"Status endpoint. Scope: {scope}", end="\n")
    print("-" * 150)

    message: Message = await receive()
    print(f"Received message: {message}")

    response_message = {
        "type": "http.response.start",
        "status": 204,
    }
    print(f"Sending response start: {response_message}")
    await send(response_message)

    response_message = {
        "type": "http.response.body",
        "body": b"",
        "more_body": False,
    }
    print(f"Sending response body: {response_message}")
    print("-" * 150)
    await send(response_message)


# curl -X POST http://127.0.0.1:8000/status
async def error_endpoint(scope: Scope, receive: Receive, send: Send) -> None:
    """Обробник ендпоінту для відправки помилки."""
    print(f"Status endpoint. Scope: {scope}", end="\n")
    print("-" * 150)

    message: Message = await receive()
    print(f"Received message: {message}")

    response_message = {
        "type": "http.response.start",
        "status": 400,
        "headers": [(b"content-type", b"application/json")],
    }
    print(f"Sending response start: {response_message}")
    await send(response_message)

    response_message = {
        "type": "http.response.body",
        "body": json.dumps({"detail": "Endpoint does not exist."}).encode("utf-8"),
        "more_body": False,
    }
    print(f"Sending response body: {response_message}")
    await send(response_message)


async def handle_websocket(scope: Scope, receive: Receive, send: Send) -> None:
    """Обробник з'єднань Websocket."""
    assert scope["type"] == "websocket"

    if scope["path"] == "/ws":
        print(f"Handle websocket. Scope: {scope}", end="\n")
        print("-" * 150)

        while True:
            print("Waiting for message...")

            message: Message = await receive()
            print(f"Received message: {message}")

            if message["type"] == "websocket.connect":
                response_message = {"type": "websocket.accept"}
                await send(response_message)
                continue

            if message["type"] == "websocket.disconnect":
                print(f"Websocket disconnected. Status code: {message['code']}")
                break

            if message["type"] == "websocket.receive":
                print(f"Websocket message: {message['text']}")
                close = False
                if json.loads(message["text"]) == {"message": "close"}:
                    response_message = {
                        "type": "websocket.close",
                        "code": 1000,
                        "reason": "Initiated by client",
                    }
                    close = True
                else:
                    response_message = {
                        "type": "websocket.send",
                        "text": message["text"],
                    }
                print(f"Sending message: {response_message}")
                await send(response_message)
                if close:
                    break

                continue


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        port=8000,
        log_level="info",
        use_colors=True,
        reload=True,
        # root_path="/api",
    )
