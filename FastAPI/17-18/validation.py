import logging
from datetime import date, datetime
from enum import StrEnum
from typing import Any, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    ModelWrapValidatorHandler,
    ValidationError,
    field_validator,
    model_validator,
)

# конфігурація логування і створення логера для модуля
logging.basicConfig(
    style="{",
    level=logging.INFO,
    handlers=(logging.StreamHandler(),),
    datefmt="%Y-%m-%d %H:%M:%S",
    format="[{levelname} - {asctime}] - {name} - {message}",
)
logger = logging.getLogger(__name__)


class EventType(StrEnum):
    """Тип події."""

    CONFERENCE = "conference"
    WORKSHOP = "workshop"
    MEETUP = "meetup"


class Location(StrEnum):
    """Місце проведення."""

    ONLINE = "online"
    OFFLINE = "offline"


class Participant(BaseModel):
    """Модель учасника."""

    # валідація поля на довжину символів (5 - 50)
    name: str = Field(..., min_length=2, max_length=50, description="Ім'я учасника.")
    # валідація поля на мінімальний вік (18 років)
    age: int = Field(..., ge=18, description="Вік учасника.")

    email: EmailStr  # автоматична валідація поля
    # може бути не передано
    phone: str | None = Field(
        default=None,
        pattern=r"\+?\d{10,15}",
        description="Номер телефону учасника.",
    )
    # може бути не передано (за замовчуванням автоматична підписка)
    newsletter_subscribed: bool = Field(
        default=True, description="Автоматична підписка на розсилку."
    )

    @field_validator("name")
    @classmethod
    def name_must_be_capitalized(cls, name: str) -> str:
        """Кастомний валідатор на поле ім'я."""
        if not name[0].isupper():
            raise ValueError("Name must start with a capital letter.")

        return name


class Event(BaseModel):
    """Модель події."""

    title: str = Field(..., min_length=5)
    description: str | None = None
    date_and_time: datetime = Field(description="Дата та час події.")
    # значення за замовчуванням Online
    location: Location = Field(
        default=Location.ONLINE, description="Місце проведення події."
    )
    event_type: EventType = Field(default=EventType.MEETUP)
    # поле автоматично буде заповнено поточною датою та часом
    created_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        json_schema_extra={
            "description": "A model that describes event details.",
            "examples": [
                {
                    "title": "PyCon",
                    "description": "Discussing about Python improvements.",
                    "location": "Online",
                    "event_type": "meetup",
                    "created_at": "2025-06-10 10:00",
                }
            ],
        },
        # поля типу datetime (date_and_time and created_at) буде форматовано автоматично в форматі дд-мм-ррр г:хв
        json_encoders={datetime: lambda x: x.strftime("%d-%m-%Y %H:%M")},
    )

    @field_validator("date_and_time")
    @classmethod
    def date_must_be_future(cls, d: date) -> date:
        """Кастомний валідатор дати події."""
        if d < datetime.now():
            raise ValueError("Event date must be in the future.")

        return d


class BookingRequest(BaseModel):
    """Модель заявки."""

    event: Event
    participants: list[Participant]
    confirmed: bool = False  # за замовчуванням заявка не підтверджена
    notes: str | None = None  # користувач може залишити коментар

    # може мати параметр mode 'after', 'before', 'wrap'
    @model_validator(mode="after")
    def check_participant_count(self) -> Self:
        """
        Загальна перевірка кількості учасників події.
        Буде запущена після перевірки всіх полів моделі.
        """
        if len(self.participants) > 3:
            raise ValueError(
                "You can't register more than 3 participants for one event."
            )
        return self  # важливо саме повернути поточний об'єкт із валідатора

    @model_validator(mode="before")
    @classmethod
    # Тип даних Any означає, що можуть бути прийняті дані будь якого класу,
    # так як цей валідатор запускається самий перший перед створенням об'єкту
    def check_card_number_not_present(cls, data: Any) -> Any:
        """Валідуємо сирі дані, перед створенням об'єкту Pydantic."""
        if isinstance(data, dict):
            if "card_number" in data:
                raise ValueError("'card_number' should not be included.")

        return data

    @model_validator(mode="wrap")
    @classmethod
    def count_notes_characters(
        cls, data: Any, handler: ModelWrapValidatorHandler[Self]
    ) -> Self:
        """Валідуємо кількість символів в полі `notes`."""
        try:
            model = handler(data)
        except ValidationError as e:
            # якщо якийсь із попередньо пройдених валідаторів видав помилку
            # то логуємо її і робимо її raise
            logging.error(
                "Errors occurred during requesting process: %s",
                e.errors(include_input=False),
            )
            raise

        # інакше робимо саме потрібну нам перевірку і знову робимо raise
        if model.notes and len(model.notes) > 20:
            raise ValueError("Notes field cannot exceed 20 characters.")

        return model


def create_valid_participant() -> Participant:
    """Створення валідного об'єкта учасника."""
    try:
        participant = Participant(
            name="John Doe",
            age=23,
            email="john.doe@example.com",
            phone="+380971234567",
        )
        return participant
    except ValidationError as e:
        raise ValueError(e.json(indent=4)) from None


def create_invalid_participant() -> Participant:
    """Створення не валідного об'єкта учасника."""
    try:
        participant = Participant(
            name="John Doe",
            age=16,  # менший вік
            email="john.doe@example.com",
            phone="+380971234",  # не вистачає символів (10-15)
        )
        return participant
    except ValidationError as e:
        raise ValueError(e.json(indent=4)) from None


def create_valid_event() -> Event:
    """Створення валідного об'єкта події."""
    try:
        event = Event(
            title="PyCon",
            description="Talking about Python features and optimization.",
            date_and_time=datetime(year=2025, month=6, day=15, hour=10, minute=0),
            event_type=EventType.CONFERENCE,
        )
        return event
    except ValidationError as e:
        raise ValueError(e.json(indent=4)) from None


def create_invalid_event() -> Event:
    """Створення не валідного об'єкта події."""
    try:
        event = Event(
            title="Py",
            # дата в минулому
            date_and_time=datetime(year=2025, month=5, day=15, hour=10, minute=0),
            event_type=EventType.CONFERENCE,
        )
        return event
    except ValidationError as e:
        raise ValueError(e.json(indent=4)) from None


def create_valid_booking_request(
    event: Event, participant: Participant
) -> BookingRequest:
    """Створення валідного об'єкта запису на подію."""
    try:
        request = BookingRequest(
            event=event,
            participants=[participant],
            confirmed=False,
            notes="Якийсь коментар.",
        )
        return request
    except ValidationError as e:
        raise ValueError(e.json(indent=4)) from None


def create_invalid_booking_request(
    event: Event, participant: Participant
) -> BookingRequest:
    """Створення не валідного об'єкта запису на подію."""
    try:
        request = BookingRequest(
            event=event,
            # більше ніж 3 учасники
            participants=[participant, participant, participant, participant],
            confirmed=True,
            notes="Якийсь коментар.",
            # поле нижче призведе до помилки валідації
            # так як валідатор 'check_card_number_not_present' одразу викличе ValueError
            # через те, що поле з таким іменем не дозволене для створення об'єкта BookingRequest
            # card_number="1234-5678-0123-7896",
        )
        return request
    except ValidationError as e:
        raise ValueError(e.json(indent=4)) from None


if __name__ == "__main__":
    created_participant = create_valid_participant()
    print(created_participant.model_dump_json(indent=4))

    # розкоментувати для перевірки створення невалідного Participant
    # create_invalid_participant()

    created_event = create_valid_event()
    print(created_event.model_dump_json(indent=4))

    # розкоментувати для перевірки створення невалідного Event
    # create_invalid_event()

    created_request = create_valid_booking_request(created_event, created_participant)
    print(created_request.model_dump_json(indent=4))

    # розкоментувати для перевірки створення невалідного BookingRequest
    # create_invalid_booking_request(created_event, created_participant)
