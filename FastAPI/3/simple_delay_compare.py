import asyncio
import time


async def simple_delay1() -> None:
    """Імітує асинхронну задачу з затримкою 5 секунд."""
    print("Початок задачі 1")
    await asyncio.sleep(5)
    print("Завершення задачі 1")


async def simple_delay2() -> None:
    """Імітує асинхронну задачу з затримкою 2 секунди."""
    print("Початок задачі 2")
    await asyncio.sleep(2)
    print("Завершення задачі 2")


async def main_gather() -> None:
    """
    Запускає дві задачі одночасно за допомогою asyncio.gather(),
    додаючи ці задачі в цикл подій (event loop).
    """
    await asyncio.gather(simple_delay1(), simple_delay2())


async def main() -> None:
    """
    Запускає дві задачі послідовно — одна за одною.
    Задачі не будуть працювати асинхронно, а будуть виконуватись
    одна за одною.
    """
    await simple_delay1()
    await simple_delay2()


if __name__ == "__main__":
    start = time.perf_counter()
    # розкоментувати рядок нижче для перевірки справжньої асинхронної роботи
    # asyncio.run(main_gather())
    # розкоментувати рядок нижче для перевірки неправильного використання асинхронної роботи
    # asyncio.run(main())
    print(f"Виконання завершено за {time.perf_counter() - start:.5f} секунд.")
