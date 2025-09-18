import csv
import os
import sqlite3


def main(file_name: str, db_name: str) -> None:
    """Функція для імпорту даних із `csv` в `sqlite` базу даних."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, file_name)

    with sqlite3.connect(db_name, autocommit=True) as connection:
        cursor = connection.cursor()

        create_table_query = """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(50) NOT NULL,
                    phone VARCHAR(50) NOT NULL,
                    email VARCHAR(50) NOT NULL,
                    age INTEGER NOT NULL
            );
            """

        cursor.execute(create_table_query)
        with open(file_path, encoding="utf-8") as file:
            contents = csv.reader(file)
            # пропускаємо заголовок
            next(contents)

            insert_records = (
                "INSERT INTO users (id, name, email, phone, age) VALUES(?, ?, ?, ?, ?);"
            )

            cursor.executemany(insert_records, contents)
            connection.commit()


if __name__ == "__main__":
    main("fake_users.csv", "./mydb.db")
