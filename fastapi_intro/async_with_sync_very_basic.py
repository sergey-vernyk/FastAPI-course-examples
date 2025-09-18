import asyncio
import random
from time import perf_counter

import httpx
import requests

# pylint: disable=C0116:missing-function-docstring


async def fetch_wiki_page_async(url: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text


async def get_wiki_page_async() -> None:
    print("Отримання сторінок вікіпедії асинхронно\n")
    wikipedia_urls = [
        "https://uk.wikipedia.org/wiki/Python",
        "https://uk.wikipedia.org/wiki/Java",
    ]
    tasks = [fetch_wiki_page_async(url) for url in wikipedia_urls]
    wikipedia_pages = await asyncio.gather(*tasks)
    for page in wikipedia_pages:
        print(page[:500])
        print()


def fetch_wiki_page_sync(url: str) -> str:
    response = requests.get(url, timeout=20)
    return response.text


def get_wiki_pages_sync() -> None:
    print("Отримання сторінок вікіпедії синхронно\n")
    wikipedia_urls = [
        "https://uk.wikipedia.org/wiki/Python",
        "https://uk.wikipedia.org/wiki/Java",
    ]
    pages = [fetch_wiki_page_sync(url) for url in wikipedia_urls]
    for page in pages:
        print(page[:500])
        print()


async def fetch_pokemons_info_async(url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()["name"]


async def get_pokemons_async(pokemons_ids: list[int]) -> None:
    print("Отримання покемонів асинхронно\n")
    pokemon_urls = [
        f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}" for pokemon_id in pokemons_ids
    ]
    tasks = [fetch_pokemons_info_async(url) for url in pokemon_urls]
    results = await asyncio.gather(*tasks)
    for result in results:
        print(result)


def fetch_pokemons_info_sync(url: str):
    response = requests.get(url, timeout=20)
    return response.json()["name"]


def get_pokemons_sync(pokemons_ids: list[int]) -> None:
    print("Отримання покемонів синхронно\n")
    pokemon_urls = [
        f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}" for pokemon_id in pokemons_ids
    ]
    results = [fetch_pokemons_info_sync(url=url) for url in pokemon_urls]
    for result in results:
        print(result)


if __name__ == "__main__":
    pokemons_ids = random.sample(range(1, 10), 5)

    # start = perf_counter()
    # asyncio.run(get_pokemons_async(pokemons_ids))
    # print(f"Estimated time: {(perf_counter() - start):.2f} seconds.")

    start = perf_counter()
    get_pokemons_sync(pokemons_ids)
    print(f"Estimated time: {(perf_counter() - start):.2f} seconds.")

    # start = perf_counter()
    # asyncio.run(get_wiki_page_async())
    # print(f"Estimated time: {(perf_counter() - start):.2f} seconds.")

    # start = perf_counter()
    # get_wiki_pages_sync()
    # print(f"Estimated time: {(perf_counter() - start):.2f} seconds.")
