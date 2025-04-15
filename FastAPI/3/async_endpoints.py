import asyncio

import httpx
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sync_async_requests import do_something_stuff

app = FastAPI()


@app.get("/async-endpoint")
async def read_items():
    """Простий асинхронний ендпоінт."""
    await asyncio.sleep(1)
    return {"message": "Асинхронна відповідь після 1 секунди очікування"}


@app.get("/users/")
async def get_users() -> JSONResponse:
    """
    Асинхронний ендпоінт, який виконує асинхронну задачу
    з іншого модуля.
    """
    users = await do_something_stuff()
    return JSONResponse(content=users, status_code=200)


async def httpx_example():
    """Приклад асинхронної функції з використанням асинхронної бібліотеки."""
    async with httpx.AsyncClient() as client:
        response = await client.get("https://jsonplaceholder.typicode.com/posts/10")

    return response.json()


if __name__ == "__main__":
    # запуск асинхронної функції (корутини) і повернення
    # результату її роботи
    result = asyncio.run(httpx_example())
    print(result)
