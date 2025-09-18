from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

html = """
    <!DOCTYPE html>
    <html>
        <head>
            <meta charset="UTF-8">
            <title>WebSocket Chat</title>
        </head>
        <body>
            <h1>WebSocket Chat</h1>
            <button onclick="connect()">Connect</button>

            <form onsubmit="sendMessage(event)">
                <input type="text" id="messageText" autocomplete="off" />
                <button type="submit">Send</button>
            </form>

            <ul id="messages"></ul>

            <script>
                let ws = null;

                function connect() {
                    ws = new WebSocket("ws://127.0.0.1:8010/ws");

                    ws.onopen = function () {
                        appendSystemMessage("Connected to chat.");
                    };

                    ws.onmessage = function (event) {
                        const messages = document.getElementById('messages');
                        const message = document.createElement('li');
                        const content = document.createTextNode(event.data);
                        message.appendChild(content);
                        messages.appendChild(message);
                    };

                    ws.onclose = function () {
                        appendSystemMessage("Disconnected from chat.");
                    };

                    ws.onerror = function () {
                        appendSystemMessage("WebSocket error.");
                    };
                }

                function sendMessage(event) {
                    event.preventDefault();
                    const input = document.getElementById("messageText");
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(input.value);
                        input.value = '';
                    } else {
                        appendSystemMessage("Not connected.");
                    }
                }

                function appendSystemMessage(text) {
                    const messages = document.getElementById('messages');
                    const message = document.createElement('li');
                    message.style.color = "gray";
                    message.textContent = text;
                    messages.appendChild(message);
                }
            </script>
        </body>
    </html>
"""


@app.get("/chat")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect as e:
        print(f"Connectio was closed. Code: {e.code}")
