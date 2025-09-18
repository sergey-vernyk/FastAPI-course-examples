import json
from datetime import date

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    HttpUrl,
    ValidationError,
    field_validator,
)


class UserPydantic(BaseModel):
    """Поля для користувача з використанням Pydantic моделі."""

    name: str = Field(description="The name of the user.")
    email: EmailStr
    date_of_birth: date
    phone_number: str = Field(pattern=r"\+?\d{10,15}")
    age: int = Field(ge=10, le=100, description="User age.")
    web_site: HttpUrl | None = None

    # кастомні валідатори для полів email та name
    @field_validator("email")
    @classmethod
    def email_validation(cls, email: str) -> str:
        """Додаткова валідація поля для електронної пошти."""
        if "@" not in email:
            raise ValueError("Email should contain @ symbol.")

        return email

    @field_validator("name")
    @classmethod
    def name_must_contain_space(cls, name: str) -> str:
        """Дані в полі `name` повинно містити пробіл."""
        if " " not in name:
            raise ValueError("Username must contain a space.")

        return name.title()

    # extra
    # frozen
    # json_schema_extra
    # title
    # str_min_length
    # regex_engine
    # json_encoders
    model_config = ConfigDict(
        title="Users API",
        # мінімальна довжина буь якої строки, визначеної в моделі повинна бути не менше 5
        str_min_length=5,
        # Якщо True, то змінювати об'єкт моделі після створення вже не можна і буде помилка, але якщо False - то можна
        frozen=False,
        # є три варіанти цього значення (allow, forbid, ignore)
        # allow - можна додавати додаткові параметри при створенні об'єкта моделі
        # forbid - не можна додавати додаткові параметри при створенні об'єкта моделі (буде помилка)
        # ignore - додані додаткові параметри просто будуть ігноруватись
        extra="forbid",
        # вибір engine для регулярних виразів (python-re або rust-regex)
        regex_engine="python-re",
        # додавання додаткових метаданих до схеми JSON (наприклад, приклади як буде виглядати ваша модель в форматі JSON)
        json_schema_extra={
            "description": "A user model including contact and web info.",
            "examples": [
                {
                    "name": "Alice",
                    "email": "alice@example.com",
                    "age": 30,
                    "web_site": "https://alice.dev",
                }
            ],
        },
        # типи енкодерів для типів даних в вашій моделі
        # (тут поле 'date_of_birth' буде в форматі дд-мм-РРРР, хоча за замовчуванням воно РРРР-мм-дд)
        json_encoders={date: lambda x: x.strftime("%d-%m-%Y")},
    )


def main() -> None:
    try:
        user_pydantic = UserPydantic(
            name="John Doe",
            email="john@example.com",
            phone_number="+380971234567",
            age=18,
            date_of_birth=date(1990, 2, 17),
            web_site=HttpUrl("http://mysite.com"),
            # field="value", # додаткове поле, яке може бути додано для перевірки налаштування extra в 'model_config'
        )
        print(user_pydantic.model_dump_json(indent=4))
        # повертає схему JSON, яка може бути використана для процесу валідації переданих даних
        # або також для авто генерування документації для Swagger UI
        print(json.dumps(user_pydantic.model_json_schema(), indent=4))
        # можна використати для перевірки налаштування frozen в 'model_config'
        user_pydantic.age = 19
        print(user_pydantic.model_dump_json(indent=4))
    except ValidationError as e:
        print(e.json(indent=4))


if __name__ == "__main__":
    main()
