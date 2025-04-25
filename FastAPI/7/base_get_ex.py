import os
from datetime import datetime, timedelta, timezone
from typing import Any

import aiohttp
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query

load_dotenv(os.path.abspath(f"{os.path.pardir}/.env"))

WEATHER_API_KEY = os.environ.get("OPENWEATHERMAP_API_KEY")
WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

app = FastAPI()

# select * from users limit 10;
# http://127.0.0.1:8000/users/?limit=2


@app.get("/users/")
async def fetch_users(
    limit: int = Query(
        default=100,
        description="Кількість користувачів для отримання.",
    ),
) -> Any:
    """Отримання інформації про всіх користувачів."""
    url = "https://jsonplaceholder.typicode.com/users"
    async with aiohttp.ClientSession() as session:
        response = await session.get(url)

        if response.status != 200:
            raise HTTPException(response.status, "Failed to fetch users data.")

    users = await response.json()
    return users[:limit]


# http://127.0.0.1:8000/users/5
@app.get("/users/{pk}")
async def fetch_user(pk: int) -> Any:
    """Отримання інформації користувача з `pk`."""
    url = f"https://jsonplaceholder.typicode.com/users/{pk}"
    async with aiohttp.ClientSession() as session:
        response = await session.get(url)

        if response.status != 200:
            raise HTTPException(response.status, "Failed to fetch user data.")

    user = await response.json()

    if not user:
        raise HTTPException(404, "User not found.")

    return user


# http://127.0.0.1:8000/weather/Kyiv
@app.get("/weather/{city}")
async def get_weather(city: str) -> dict[str, Any]:
    """Отримання погоди для міста `city`."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            WEATHER_URL,
            params={
                "q": city,
                "appid": WEATHER_API_KEY,
                "units": "metric",
                "lang": "ua",
            },
        )

    response = response.json()

    if response["cod"] == "404":
        raise HTTPException(404, response["message"])

    current_timezone = response["timezone"]

    weather_data = {
        "Країна": response["sys"]["country"],
        "Назва міста": response["name"],
        "Температура": f"{response['main']['temp']} °C",
        "Мінімальна температура": f"{response['main']['temp_min']} °C",
        "Максимальна температура": f"{response['main']['temp_max']} °C",
        "Тиск": f"{response['main']['pressure']} гПа",
        "Вологість": f"{response['main']['humidity']} %",
        "Швидкість вітру": f"{response['wind']['speed']} м/с",
        "Схід сонця": datetime.fromtimestamp(
            response["sys"]["sunrise"] + current_timezone, tz=timezone.utc
        ).strftime("%H:%M"),
        "Захід сонця": datetime.fromtimestamp(
            response["sys"]["sunset"] + current_timezone, tz=timezone.utc
        ).strftime("%H:%M"),
        "Тривалість дня": str(
            timedelta(seconds=response["sys"]["sunset"] - response["sys"]["sunrise"])
        ),
        "Поточний час": datetime.fromtimestamp(
            response["dt"] + current_timezone, tz=timezone.utc
        ).strftime("%d-%m-%Y %H:%M"),
    }
    return weather_data
