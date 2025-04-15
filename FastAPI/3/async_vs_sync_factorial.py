import asyncio
from time import perf_counter


async def async_factorial(n):
    """Асинхронна функція для обчислення факторіалу числа."""
    if n == 0:
        return 1

    return n * await async_factorial(n - 1)


def sync_factorial(n):
    """Синхронна функція для обчислення факторіалу числа."""
    if n == 0:
        return 1

    return n * sync_factorial(n - 1)


if __name__ == "__main__":
    # Вимірювання часу для синхронного обчислення факторіалу
    start = perf_counter()
    result = sync_factorial(10)
    sync_estimated_time = perf_counter() - start
    print(f"Факторіал 10 синхронно = {result} за {sync_estimated_time:.10f} секунди.")

    # Вимірювання часу для асинхронного обчислення факторіалу
    start = perf_counter()
    result = asyncio.run(async_factorial(10))
    async_estimated_time = perf_counter() - start
    print(f"Факторіал 10 асинхронно = {result} за {async_estimated_time:.10f} секунди.")

    print(
        f"Різниця між асинхронним та синхронним  обчисленням: {async_estimated_time / sync_estimated_time:.2f} разів."
    )
