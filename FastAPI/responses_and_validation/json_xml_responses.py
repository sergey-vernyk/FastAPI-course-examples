import aiosqlite
from fastapi import Depends, FastAPI, HTTPException, Response, status
from models import DepartmentCreate, DepartmentInfo, EmployeeCreate

SQLITE_DB_NAME = "corporation.db"


async def get_connection():
    """Створюємо та повертаємо об'єкт з'єднання."""
    async with aiosqlite.connect(SQLITE_DB_NAME) as connection:
        connection.row_factory = aiosqlite.Row
        yield connection
        await connection.close()


async def create_tables() -> None:
    """Створення таблиць в БД при старті програми та автоматичне закриття з'єднання після завершення."""
    async with aiosqlite.connect(SQLITE_DB_NAME) as connection:
        cursor: aiosqlite.Cursor = await connection.cursor()
        await cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS employees (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    name            VARCHAR(30) NOT NULL,
                    email           VARCHAR(50) NOT NULL,
                    job_title       VARCHAR(30) NOT NULL,
                    salary          INTEGER,
                    department_id   INTEGER,
                    FOREIGN KEY (department_id) REFERENCES departments(id)
                );
            """
        )
        await cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS departments (
                    id      INTEGER PRIMARY KEY AUTOINCREMENT,
                    name    VARCHAR(50) UNIQUE NOT NULL
                );
            """
        )
        await connection.commit()


app = FastAPI(on_startup=(create_tables,), title="Corporation personal API.")


# http://127.0.0.1:8000/departments/
# curl -i -X POST 'http://127.0.0.1:8000/departments/' \
# -H 'Content-Type: application/json' \
# -d '{ "name": "logistic"}'
@app.post(
    "/departments/",
    status_code=status.HTTP_201_CREATED,
    response_model=DepartmentInfo,
)
async def create_department(
    data: DepartmentCreate, connection: aiosqlite.Connection = Depends(get_connection)
) -> DepartmentInfo:
    """Створення підрозділу та повернення стандартної відповіді в JSON."""

    print(f"Дані для створення підрозділу: {data.model_dump()}")

    async with connection.cursor() as cursor:
        await cursor.execute("SELECT id FROM departments WHERE name = ?;", (data.name,))
        db_department = await cursor.fetchone()

        if db_department is not None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Department exists.")

        await cursor.execute(
            "INSERT INTO departments (name) VALUES (?) RETURNING id;", (data.name,)
        )
        last_inserted = await cursor.fetchone()
        await connection.commit()

    return DepartmentInfo(id=last_inserted["id"], name=data.name)


# http://127.0.0.1:8000/employees/
# curl -i -X POST 'http://127.0.0.1:8000/employees/' \
# -H 'Content-Type: application/json' \
# -d '{ "name": "John Doe", "email": "john.doe@example.com", "job_title": "developer", "salary": 1500, "department_id": 2 }'


# curl -i -X POST 'http://127.0.0.1:8000/employees/' \
# -H 'Content-Type: application/json' \
# -d '{ "name": "John Doe", "email": "john.doe.example.com", "job_title": "other", "salary": 1500, "department_id": 2 }'
@app.post(
    "/employees/",
    status_code=status.HTTP_201_CREATED,
    response_class=Response,
)
async def create_employee(
    data: EmployeeCreate, connection: aiosqlite.Connection = Depends(get_connection)
) -> Response:
    """Створення співробітника та повернення відповіді в форматі XML."""

    print(f"Дані для створення співробітника: {data.model_dump()}")

    async with connection.cursor() as cursor:
        await cursor.execute("SELECT id FROM employees WHERE email = ?;", (data.email,))
        db_employee = await cursor.fetchone()

        if db_employee is not None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Employee exists.")

        await cursor.execute(
            "INSERT INTO employees (name, email, job_title, salary, department_id) VALUES (?, ?, ?, ?, ?) RETURNING *;",
            (data.name, data.email, data.job_title, data.salary, data.department_id),
        )
        last_inserted = await cursor.fetchone()
        await connection.commit()

        xml_content = None

        if last_inserted is not None:
            xml_content = f"""
                <employee>
                    <id>{last_inserted["id"]}</id>
                    <name>{last_inserted["name"]}</name>
                    <email>{last_inserted["email"]}</email>
                    <job_title>{last_inserted["job_title"]}</job_title>
                    <salary>{last_inserted["salary"]}</salary>
                    <department_id>{last_inserted["department_id"]}</department_id>
                </employee>
            """

    return Response(content=xml_content, media_type="application/xml")
