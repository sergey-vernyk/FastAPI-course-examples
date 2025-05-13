import asyncio
from collections import defaultdict
from typing import Any

import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, HttpUrl

# https://books.toscrape.com/


class UrlToScrap(BaseModel):
    """Модель для даних адреси сайту для парсингу."""

    url: HttpUrl


app = FastAPI(title="Parser API")


@app.get("/pages/")
async def get_page(
    url: HttpUrl = Query(..., description="Адреса сторінки для отримання контенту."),
) -> dict[Any, Any]:
    """Отримує список категорій книг зі сторінки з головного меню (sidebar)."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url.encoded_string(), follow_redirects=True)
        if not response.is_success:
            raise HTTPException(response.status_code, response.text)

    content = response.content
    soup = BeautifulSoup(content, "lxml")
    sidebar = soup.find(class_="sidebar col-sm-4 col-md-3")
    ul_elements = sidebar.find_all("ul")

    categories_urls: dict[str, str] = {}

    for ul in ul_elements:
        for li in ul.find_all("li"):
            link = li.find("a")
            if link:
                categories_urls[link.getText(strip=True)] = (
                    f"{url.scheme}://{url.host}/{link.get('href')}"
                )

    return categories_urls


@app.post("/pages/parse")
async def parse_pages(urls: list[UrlToScrap]) -> defaultdict[str, list[dict[str, Any]]]:
    """
    Парсить сторінки книг, проходить по пагінації та повертає дані по книгах
    згруповані за категоріями.
    """
    try:
        first_pages = await get_pages([url.url for url in urls])
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e

    next_pages_urls = []
    for page in first_pages:
        soup = BeautifulSoup(page.content, "lxml")

        if pager := soup.find("ul", class_="pager"):
            number_of_pages = int(
                pager.find_next("li", class_="current").get_text(strip=True).split()[-1]
            )
            for n in range(1, number_of_pages + 1):
                if n == 1:
                    continue

                next_pages_urls.append(
                    HttpUrl(
                        f"{page.request.url.scheme}://{page.request.url.host}{'/'.join(page.request.url.path.split('/')[:-1])}/page-{n}.html"
                    )
                )
    try:
        all_pages = first_pages + await get_pages(next_pages_urls)
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e

    books_info = defaultdict(list[Any])

    for page in all_pages:
        soup = BeautifulSoup(page.content, "lxml")
        books_section = soup.find(class_="col-sm-8 col-md-9")

        book_category = books_section.find("div", class_="page-header action").get_text(
            strip=True
        )

        ol = books_section.find("ol", class_="row")

        for li in ol.find_all("li"):
            title = li.find("h3").find("a").get("title")
            price = li.select_one("p.price_color").text.strip()
            in_stock = li.select_one("p.instock.availability").get_text(strip=True)
            rating_raw = li.find("p", class_="star-rating").get("class")[-1]

            rating_to_digit = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
            books_info[book_category].append(
                {
                    "title": title,
                    "price": price,
                    "rating": rating_to_digit[rating_raw],
                    "in_stock": bool(in_stock),
                }
            )

    return books_info


async def get_pages(urls: list[HttpUrl]) -> list[httpx.Response]:
    """Асинхронно отримує вміст сторінок за списком URL-адрес."""
    async with httpx.AsyncClient() as client:
        try:
            tasks = [client.get(url.encoded_string()) for url in urls]
            responses = await asyncio.gather(*tasks)
        except httpx.RequestError as e:
            raise e

    return responses
