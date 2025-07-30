from datetime import date
from enum import StrEnum

from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    ValidationError,
    conlist,
    field_validator,
)


class UserTypeEnum(StrEnum):
    ADMIN = "admin"
    USER = "user"


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
    web_site: HttpUrl | None = None  # noqa: F821

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
    class ProductList(BaseModel):
        product_names: conlist(str, min_length=2, max_length=10)

    data = {"product_names": ["Apple", "Banana", "Cherry", "Date", "Elderberry"]}

    try:
        product_list = ProductList(**data)
        print(product_list)
    except ValidationError as e:
        print(e.json(indent=4))

    invalid_data = {
        # не спрацює, так як валідація працює відносно кількості елементів в списку, а не кількості символів в одному елементі списку.
        "product_names": ["A", "VeryLongProductNameExceedingLengthLimit", "Kiwi"]
        # "product_names": ["Kiwi"]
    }

    try:
        product_list = ProductList(**invalid_data)
        print(product_list)
    except ValidationError as e:
        print("Невалідні дані були виявлені:")
        print(e.json(indent=4))


if __name__ == "__main__":
    main()
