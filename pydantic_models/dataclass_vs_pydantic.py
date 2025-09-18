from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    HttpUrl,
    ValidationError,
    field_validator,
)


class UserTypeEnum(StrEnum):
    ADMIN = "admin"
    USER = "user"


@dataclass
class UserDataclass:
    """Поля для користувача з використанням датакласу."""

    name: str
    email: str
    age: int
    hobbies: list["Hobby"] = field(default_factory=list)
    web_site: HttpUrl | None = field(default=None)


class Hobby(BaseModel):
    """Поля для хобі з використанням Pydantic моделі."""

    name: str
    description: str | None = None
    difficulty: int = Field(default=0, ge=0, lt=10)
    started_at: date = Field(description="Date when this became a hobby.")


class UserPydantic(BaseModel):
    """Поля для користувача з використанням Pydantic моделі."""

    name: str = Field(description="The name of the user.")
    role: UserTypeEnum = Field(
        default=UserTypeEnum.USER,
        description="Role of the user in the system.",
    )
    email: str = Field(min_length=3, max_length=50, examples=["example@example.com"])
    # email: EmailStr
    age: int = Field(ge=10, le=100, description="User age.")
    hobbies: list[Hobby] = Field(
        default_factory=list,
        description="Hobbies of the user.",
    )
    web_site: HttpUrl | None = None

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


def main() -> None:
    hobby1 = hobby2 = hobby3 = None
    user_pydantic = None

    # створення об'єктів Hobby з валідацією
    try:
        hobby1 = Hobby(
            name="Painting",
            description="Creating art with watercolors and acrylics.",
            difficulty=4,
            started_at=date(2023, 3, 15),
        )

        hobby2 = Hobby(
            name="Cycling",
            description="Riding a bicycle for exercise and fun.",
            difficulty=5,
            started_at=date(2021, 6, 10),
        )

        hobby3 = Hobby(
            name="Coding",
            description="Writing programs in Python.",
            difficulty=7,
            started_at=date(2020, 1, 20),
        )
    except ValidationError as e:
        print(e.json(indent=4))

    # створення об'єкту користувача із валідацією
    try:
        user_pydantic = UserPydantic(
            name="John Doe",
            email="john@example.com",
            age=18,
            web_site=HttpUrl("http://mysite.com"),
            hobbies=[hobby1, hobby2, hobby3],
        )
        print(user_pydantic.model_dump_json(indent=4))
    except ValidationError as e:
        print(e.json(indent=4))

    # створення об'єкту користувача як датакласу
    user_dataclass = UserDataclass(name="John", email="john@example.com", age=18)
    print(user_dataclass)

    # конвертація із JSON в об'єкт Pydantic
    json_data = """
    {
        "name": "Coding" ,
        "description": "I like coding!",
        "difficulty": 7,
        "started_at": "2024-10-12"
    }
    """
    hobby = Hobby.model_validate_json(json_data)
    print(hobby.model_dump())

    # конвертація з Python словника в Pydantic модель
    dict_data = {
        "name": "Coding",
        "description": "I like coding!",
        "difficulty": 7,
        "started_at": "2024-10-12",
    }
    hobby = Hobby.model_validate(dict_data)
    print(hobby.model_dump())


if __name__ == "__main__":
    main()
