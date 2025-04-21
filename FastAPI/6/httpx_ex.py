import asyncio

import httpx


async def get_users():
    """
    Отримання користувачів з БД, яка працює разом з власним
    запущеним сервером FastAPI.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get("http://127.0.0.1:8000/users/")
        # роздрукуємо статус код від сервера і тип повернутого контенту (JSON в цьому випадку)
        print("Status:", response.status_code)
        print("Content-type:", response.headers["content-type"])
        users = response.json()

    return users


async def get_post(pk: int):
    """Отримання посту по ID із стороннього API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://jsonplaceholder.typicode.com/posts/{pk}")

    return response.json()


if __name__ == "__main__":
    # перевірка запиту на отримання користувачів із власного API
    # не забудьте запустити власний сервер FastAPI перед запуском цієї задачі
    # наприклад, сервер в модулі 'aiopg_ex.py' aбо в модулі 5/aiomysql_pool.py
    users = asyncio.run(get_users())
    print(users)

    # перевірка на отримання посту із стороннього API
    post = asyncio.run(get_post(10))
    print(post)
