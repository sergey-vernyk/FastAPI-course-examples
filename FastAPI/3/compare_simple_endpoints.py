import asyncio
import time

from fastapi import FastAPI

app = FastAPI()


@app.get("/sync")
def sync_endpoint():
    """
    Самий простий синхронний ендпоінт,
    з блокуючою `time.sleep(2)` функцією.
    """
    start = time.perf_counter()
    time.sleep(2)
    return {
        "message": f"Синхронний запит завершений. Час виконання {time.perf_counter() - start:.5f} секунди."
    }


@app.get("/async")
async def async_endpoint():
    """
    Самий простий асинхронний ендпоінт
    з неблокуючої функцією (корутиною) `asyncio.sleep(2)`
    """
    start = time.perf_counter()
    await asyncio.sleep(2)
    return {
        "message": f"Асинхронний запит завершений. Час виконання {time.perf_counter() - start:.5f} секунди."
    }
