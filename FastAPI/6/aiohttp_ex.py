import asyncio
import json

import aiohttp
from aiohttp import web

users = ["serhii", "olha", "dmytro"]


async def handle_get(request: web.Request) -> web.Response:
    """Отримуємо користувача з списку `users` по імені."""
    name = request.match_info.get("name", "")

    if not name:
        return web.json_response({"error": "User name is required."}, status=400)

    if name not in users:
        return web.json_response({"error": f"User {name} does not exist."}, status=404)

    return web.json_response({"message": f"User {name} exists."})


async def handle_post(request: web.Request) -> web.Response:
    """Додаємо користувача в список `users`."""
    data = await request.json()
    user_name = data.get("user_name")

    if not user_name:
        return web.json_response({"error": "Missing user_name."}, status=400)

    if user_name in users:
        return web.json_response({"error": "User already exists."}, status=400)

    users.append(user_name)

    return web.json_response(
        {"message": "User created successfully", "user": user_name}, status=200
    )


# створення wbb сервера aiohttp (схоже як створюється FastAPI сервер)
app = web.Application()
# визначення роутів веб сервера (аналог в FastAPI @app.get("/get_user/{name}/"), @app.post("/add_user/"))
app.add_routes(
    [
        web.get("/get_user/{name}/", handler=handle_get),
        web.post("/add_user/", handler=handle_post),
    ]
)


async def get_users():
    """
    Отримання користувачів із БД на своєму працюючому сервері FastAPI.
    з використанням контекстного менеджера `with`.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get("http://127.0.0.1:8000/users/") as response:
            print("Status:", response.status)
            print("Content-type:", response.headers["content-type"])
            users = await response.json()

    return users


async def get_pokemons(ids) -> str:
    """Отримання покемонів по переданим ID без використання контекстного менеджера `with`."""
    # створення клієнтської сесії із базовим URL
    session = aiohttp.ClientSession(base_url="https://pokeapi.co")
    # створюємо список URL вигляду https://pokeapi.co/api/v2/pokemon/1
    urls = [f"/api/v2/pokemon/{pokemon_id}" for pokemon_id in ids]
    # збираємо всі функції (корутини) для виконання запитів в асинхронному режимі
    responses = await asyncio.gather(*[session.get(url) for url in urls])
    # отримаємо відповіді в форматі JSON від серверу
    pokemons_data = [await response.json() for response in responses]
    # обов'язково закриваємо сесію
    await session.close()
    # використовуємо 'dumps' для гарного відображення результату
    return json.dumps([data["name"] for data in pokemons_data], indent=4)


if __name__ == "__main__":
    # розкоментувати необхідні строки

    # запуск сервера aiohttp
    print(users)
    web.run_app(app, port=8005)
    print(users)

    # отримання користувачів із БД власного сервера FastAPI
    # не забудьте запустити власний сервер FastAPI перед запуском цієї задачі
    # наприклад, сервер в модулі 'aiopg_ex.py' aбо в модулі 5/aiomysql_pool.py

    # result = asyncio.run(get_users())
    # print(result)

    # отримання імен покемонів з ID 1-9
    # result = asyncio.run(get_pokemons(range(1, 10)))
    # print(result)
