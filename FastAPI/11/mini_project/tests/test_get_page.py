import httpx
import pytest

# file settings.json in .vscode directory
# "python.testing.pytestArgs": ["."]
# "python.testing.pytestEnabled": true
# "python.testing.cwd": "${workspaceFolder}/FastAPI/11/mini_project/"
# "python.envFile": "${workspaceFolder}/FastAPI/.env"

# pip install pytest pytest-asyncio
# uvicorn main:app --reload

BACKEND_BASE_URL = "http://127.0.0.1:8000"


@pytest.mark.asyncio
async def test_get_page_without_passing_url() -> None:
    async with httpx.AsyncClient(base_url=BACKEND_BASE_URL) as client:
        response = await client.get("/pages/", params={"url": ""})

    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "url_parsing",
                "loc": ["query", "url"],
                "msg": "Input should be a valid URL, input is empty",
                "input": "",
                "ctx": {"error": "input is empty"},
            }
        ]
    }


@pytest.mark.asyncio
async def test_get_page_page_not_found() -> None:
    async with httpx.AsyncClient(base_url=BACKEND_BASE_URL) as client:
        response = await client.get(
            "/pages/", params={"url": "https://books.toscrape.com/not_found.html"}
        )

    assert response.status_code == 404
    assert "Not Found" in response.text


@pytest.mark.asyncio
async def test_get_page_return_categories_url() -> None:
    async with httpx.AsyncClient(base_url=BACKEND_BASE_URL) as client:
        response = await client.get(
            "/pages/", params={"url": "https://books.toscrape.com"}
        )
    assert response.headers.get("Content-Type") == "application/json"
    response_data = response.json()
    assert response.status_code == 200
    assert len(response_data) == 51
    assert {"Academic", "Music", "Travel", "Philosophy", "Science"} & set(
        response_data.keys()
    )


@pytest.mark.asyncio
async def test_parse_pages() -> None:
    async with httpx.AsyncClient(base_url=BACKEND_BASE_URL) as client:
        response = await client.post(
            "/pages/parse",
            json=[
                {
                    "url": "https://books.toscrape.com/catalogue/category/books/travel_2/index.html"
                },
                {
                    "url": "https://books.toscrape.com/catalogue/category/books/mystery_3/index.html"
                },
            ],
        )
    assert response.headers.get("Content-Type") == "application/json"
    response_data = response.json()
    assert response.status_code == 200
    assert "Travel" in response_data.keys()
    assert "Mystery" in response_data.keys()

    assert len(response_data["Travel"]) == 11
    assert len(response_data["Mystery"]) == 32


@pytest.mark.asyncio
async def test_parse_pages_books_attributes() -> None:
    async with httpx.AsyncClient(base_url=BACKEND_BASE_URL) as client:
        response = await client.post(
            "/pages/parse",
            json=[
                {
                    "url": "https://books.toscrape.com/catalogue/category/books/travel_2/index.html"
                },
            ],
        )
    assert response.headers.get("Content-Type") == "application/json"
    response_data = response.json()
    assert response.status_code == 200
    assert "Travel" in response_data.keys()
    assert {"title", "price", "rating", "in_stock"} & set(response_data["Travel"][0])


@pytest.mark.asyncio
async def test_parse_pages_invalid_url() -> None:
    async with httpx.AsyncClient(base_url=BACKEND_BASE_URL) as client:
        response = await client.post(
            "/pages/parse",
            json=[
                {
                    "url": "https://books.toscrape.com/catalogue/category/books/travel_2index.html"  # помилка
                },
            ],
        )
    assert response.headers.get("Content-Type") == "text/plain; charset=utf-8"
    assert response.status_code == 500
    assert response.text == "Internal Server Error"
