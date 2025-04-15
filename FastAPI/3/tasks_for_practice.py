import asyncio

import httpx
from fastapi import FastAPI, File, UploadFile

# openweathermap.org
WEATHER_API_KEY = "YOUR_API_KEY"


app = FastAPI()


@app.get("/get-post/{post_id}")
async def get_post(post_id: int):
    """Асинхронне отримання поста по його ID."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://jsonplaceholder.typicode.com/posts/{post_id}"
        )
    return response.json()


@app.get("/get-multiple-posts")
async def get_multiple_posts():
    """Асинхронне отримання декількох постів по їх ID."""
    async with httpx.AsyncClient() as client:
        posts = await asyncio.gather(
            client.get("https://jsonplaceholder.typicode.com/posts/1"),
            client.get("https://jsonplaceholder.typicode.com/posts/2"),
            client.get("https://jsonplaceholder.typicode.com/posts/3"),
        )
    return [post.json() for post in posts]


@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(None)):
    """
    Завантаження зображення із файлової системи,
    в поточну директорії.
    """
    with open(f"uploaded_{file.filename}", "wb") as f:
        content = await file.read()
        f.write(content)

    return {"filename": file.filename}


@app.get("/weather")
async def get_weather(city: str):
    """Отримання погоди для міста `city` з ресурсу `openweathermap.org`."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://api.openweathermap.org/geo/1.0/direct",
            params={"q": city, "appid": WEATHER_API_KEY},
        )

    data = response.json()[0]
    lat = data["lat"]
    lon = data["lon"]

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "lat": lat,
                "lon": lon,
                "appid": WEATHER_API_KEY,
                "units": "metric",
                "lang": "ua",
            },
        )

    return response.json()
