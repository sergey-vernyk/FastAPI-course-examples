from enum import StrEnum

from pydantic import BaseModel, EmailStr, field_validator


class JobTitles(StrEnum):
    """Посади для співробітників."""

    DEVELOPER = "developer"
    TESTER = "tester"
    HR = "hr"
    COPYWRITER = "copywriter"
    MANAGER = "manager"
    ANALYST = "analyst"


class DepartmentCreate(BaseModel):
    """Поля для створення підрозділу."""

    name: str


class DepartmentInfo(BaseModel):
    """Поля для отримання інформації про підрозділ."""

    id: int
    name: str


class EmployeeCreate(BaseModel):
    """Поля для створення співробітника."""

    name: str
    email: str
    job_title: JobTitles
    salary: float
    department_id: int

    @field_validator("email")
    @classmethod
    def email_validation(cls, email: str) -> str:
        """Додаткова валідація поля для електронної пошти."""
        if "@" not in email:
            raise ValueError("Email should contain @ symbol.")

        return email


class EmployeeInfo(BaseModel):
    """Поля для отримання інформації про співробітника."""

    id: int
    name: str
    # стандартна валідація пошти за допомогою поля EmailStr
    email: EmailStr
    job_title: JobTitles
    salary: float
    department_id: int
