import asyncio
import json
import time

import httpx
import requests


async def do_something_stuff():
    """
    Асинхронна функція, яка виконує кілька запитів одночасно за допомогою `asyncio.gather()`
    та повертає результат виконання в змінну `res`.
    """
    print("Do stuff function.")
    res = await asyncio.gather(*[get_data_async(pk) for pk in range(1, 16)])
    print("End doing stuff function.")
    return res


async def get_data_async(pk):
    """Асинхронно отримує дані для конкретного поста за його ID з API."""
    print("Get async data.")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://jsonplaceholder.typicode.com/posts/{pk}")

    return response.json()


def get_data_sync(pk):
    """
    Синхронно отримує дані для конкретного поста за його ID з API.
    Використовується блокуюча бібліотека `requests`.
    """
    print("Get sync data.")
    response = requests.get(
        f"https://jsonplaceholder.typicode.com/posts/{pk}", timeout=10
    )
    return response.json()


def do_sync():
    """
    Синхронна функція, яка викликає запити один за одним для постів від 1 до 15.
    Запити будуть робитись за допомогою блокуючої бібліотеки `requests`.
    """
    return [get_data_sync(pk) for pk in range(1, 16)]


async def do_async() -> None:
    """Асинхронна функція, яка імітує затримку (наприклад, чекає 3 секунди)."""
    print("Start sleep.")
    # розкоментувати рядок нижче для прикладу роботи синхронного коду (time.sleep(3) блокуюча функція)
    # time.sleep(3)
    # розкоментувати рядок нижче для прикладу роботи асинхронного коду (asyncio.sleep(3) неблокуюча функція)
    await asyncio.sleep(3)
    print("End sleep.")


async def main():
    """
    Основна асинхронна функція, яка викликає `do_async()` та `do_something_stuff()`.
    в циклі подій (event loop) і повертає результат їх роботи.
    """
    return await asyncio.gather(do_async(), do_something_stuff())


if __name__ == "__main__":
    start = time.perf_counter()
    # розкоментувати рядок нижче для прикладу роботи синхронного підходу
    # result = do_sync()
    # розкоментувати рядок нижче для прикладу роботи асинхронного підходу
    result = asyncio.run(main())
    print(f"Data: {json.dumps(result, indent=2)}")
    print(f"Виконання завершено за {time.perf_counter() - start:.2f} секунд.")
