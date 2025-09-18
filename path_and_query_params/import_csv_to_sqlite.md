### Процес імпорту із файлу `csv` в базу даних `sqlite`

1. Спочатку треба запустити сервер `FastAPI`:
   ```bash
   uvicorn main:app --reload
   ```
2. Одразу в цій же папці з'явиться файл бази даних `SQLite`. В нашому випадку це буде БД з іменем `mydb.db`
3. Далі в іншому відкритому терміналі переходимо до папки із нашим файлом для імпорту `sqlite_import.py`, що також знаходиться разом з нашим файлом із `FastAPI` кодом (файл `main.py`) і файлом `fake_users.csv`.
4. Запускаємо команду:
    ```bash
    python sqlite_import.py
    ```
5. В результаті в нашій БД `mydb.db` з'являть записи із файлу `fake_users.csv`. Перевірити це можна через ендпоінт `http://127.0.0.1:8000/users/?skip=0&limit=5`. Якщо в результаті отримаєте наступне, то імпорт пройшов успішно:
    ```json
    [
        {
            "id": 1,
            "name": "Spencer Rodriguez",
            "phone": "+1-234-567-8901",
            "email": "andrealarsen@martinez-martinez.com",
            "age": 25
        },
        {
            "id": 2,
            "name": "Joseph Moore",
            "phone": "+1-345-678-9012",
            "email": "gnelson@caldwell.com",
            "age": 34
        },
        {
            "id": 3,
            "name": "Karen Singleton",
            "phone": "+1-456-789-0123",
            "email": "williamsbenjamin@flores-miller.com",
            "age": 29
        },
        {
            "id": 4,
            "name": "Julie Miller",
            "phone": "+1-567-890-1234",
            "email": "kristina62@kelley.info",
            "age": 41
        },
        {
            "id": 5,
            "name": "John Hill",
            "phone": "+1-678-901-2345",
            "email": "robertsontammy@hotmail.com",
            "age": 37
        }
    ]
    ```