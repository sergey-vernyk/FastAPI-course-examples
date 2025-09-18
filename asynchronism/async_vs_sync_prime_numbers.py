import asyncio
from time import perf_counter


async def async_prime_number(number: int) -> bool:
    """Асинхронна функція для перевірки чи передане число просте."""
    if number > 1:
        for num in range(2, number // 2 + 1):
            if number % num == 0:
                return False
        return True

    return False


def sync_prime_number(number: int):
    """Синхронна функція для перевірки чи передане число просте."""
    if number > 1:
        for num in range(2, number // 2 + 1):
            if number % num == 0:
                return False

        return True

    return False


if __name__ == "__main__":
    # Вимірювання часу для синхронної перевірки числа на простоту (CPU bound task)
    start = perf_counter()
    result = sync_prime_number(10)
    sync_estimated_time = perf_counter() - start
    print(
        f"Перевірка числа 10 на простоту синхронно = {result} за {sync_estimated_time:.10f} секунди."
    )

    # Вимірювання часу для асинхронної перевірки числа на простоту (CPU bound task)
    start = perf_counter()
    result = asyncio.run(async_prime_number(10))
    async_estimated_time = perf_counter() - start
    print(
        f"Перевірка числа 10 на простоту асинхронно = {result} за {async_estimated_time:.10f} секунди."
    )

    print(
        f"Різниця між асинхронною та синхронною перевіркою {async_estimated_time / sync_estimated_time:.2f} разів."
    )
