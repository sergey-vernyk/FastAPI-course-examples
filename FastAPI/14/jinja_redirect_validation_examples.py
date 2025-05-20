import logging

import aiosqlite
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from models import DepartmentInfo, EmployeeCreate, EmployeeInfo
from starlette.templating import _TemplateResponse

# задання назви директорії для HTML сторінок
templates = Jinja2Templates(directory="templates")

# конфігурація логування і створення логера для модуля
logging.basicConfig(
    style="{",
    level=logging.INFO,
    handlers=(logging.StreamHandler(),),
    datefmt="%Y-%m-%d %H:%M:%S",
    format="[{levelname} - {asctime}] - {name} - {message}",
)
logger = logging.getLogger(__name__)

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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Кастомний обробник помилок валідації.
    Буде викликаний автоматично, коли з'явиться помилка валідації з кодом 422.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "message": "Invalid input",
            "errors": [
                {"field": ".".join(map(str, error["loc"])), "message": error["msg"]}
                for error in exc.errors()
            ],
        },
    )


# Використання кастомного обробника помилок валідації
# Було

#   "detail": [
#     {
#       "type": "value_error",
#       "loc": [
#         "body",
#         "email"
#       ],
#       "msg": "Value error, Email should contain @ symbol.",
#       "input": "string",
#       "ctx": {
#         "error": {}
#       }
#     }
#   ]
# }

# Стало

# {
#   "message": "Invalid input",
#   "errors": [
#     {
#       "field": "body.email",
#       "message": "Value error, Email should contain @ symbol."
#     }
#   ]
# }


# http://127.0.0.1:8000/employees/
# curl -i -X GET http://127.0.0.1:8000/employees/
@app.get(
    "/employees/",
    name="get_employees",
    status_code=status.HTTP_200_OK,
    response_class=_TemplateResponse,
)
async def get_employees(
    request: Request,
    connection: aiosqlite.Connection = Depends(get_connection),
) -> HTMLResponse:
    """Отримання всіх співробітників в HTML відповіді (Jinja2)."""
    async with connection.cursor() as cursor:
        await cursor.execute(
            "SELECT id, name, email, job_title, salary, department_id FROM employees;"
        )
        db_employees = await cursor.fetchall()

        return templates.TemplateResponse(
            request=request,
            name="employees.html",
            context={
                "employees": [
                    EmployeeInfo(**employee).model_dump() for employee in db_employees
                ]
            },
        )


# http://127.0.0.1:8000/departmnets/
# curl -i -X GET http://127.0.0.1:8000/departments/
@app.get(
    "/departments/",
    status_code=status.HTTP_200_OK,
    response_class=JSONResponse,
)
async def get_departments(
    connection: aiosqlite.Connection = Depends(get_connection),
) -> JSONResponse:
    """Отримання всіх підрозділів в JSONResponse."""
    async with connection.cursor() as cursor:
        await cursor.execute("SELECT * FROM departments;")
        db_departments = await cursor.fetchall()

    departments = [DepartmentInfo(**info).model_dump() for info in db_departments]
    return JSONResponse(departments, status.HTTP_200_OK)


# curl -i -X DELETE http://127.0.0.0.1:8000/employees/<employee_id>
@app.delete(
    "/employees/{employee_id}",
    status_code=status.HTTP_303_SEE_OTHER,
    response_class=RedirectResponse,
)
async def delete_employee(
    request: Request,
    employee_id: int,
    connection: aiosqlite.Connection = Depends(get_connection),
) -> RedirectResponse:
    """
    Отримання всіх підрозділів в JSONResponse і переадресація на HTML сторінку із списком співробітників.
    """
    async with connection.cursor() as cursor:
        await cursor.execute("SELECT 1 FROM employees WHERE id = ?;", (employee_id,))
        db_employee = await cursor.fetchone()

        if db_employee is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Employee not found.")

        await cursor.execute("DELETE FROM employees WHERE id = ?;", (employee_id,))
        await connection.commit()

    return RedirectResponse(
        str(request.url_for("get_employees")), status.HTTP_303_SEE_OTHER
    )


# curl -i -X POST 'http://127.0.0.1:8000/employees/' \
# -H 'Content-Type: application/json' \
# -d '{ "name": "John Doe", "email": "john.doe.example.com", "job_title": "other", "salary": 1500, "department_id": 2 }'
@app.post(
    "/employees/", status_code=status.HTTP_201_CREATED, response_model=EmployeeInfo
)
async def create_employee(
    data: EmployeeCreate, connection: aiosqlite.Connection = Depends(get_connection)
) -> EmployeeInfo | JSONResponse:
    """Створення співробітника і логування помилки."""
    async with connection.cursor() as cursor:
        try:
            await cursor.execute(
                "SELECT id FROM employees WHERE email = ?;", (data.email,)
            )
            db_employee = await cursor.fetchone()

            if db_employee is not None:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Employee exists.")

            await cursor.execute(
                "INSERT INTO employees (name, email, job_title, salary, department_id) VALUES (?, ?, ?, ?, ?) RETURNING *;",
                (
                    data.name,
                    data.email,
                    data.job_title,
                    data.salary,
                    data.department_id,
                ),
            )
            last_inserted = await cursor.fetchone()
            await connection.commit()
        except Exception:
            logging.exception("Unexpected error.")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"message": "Internal Server Error."},
            )

    return EmployeeInfo(**last_inserted)
