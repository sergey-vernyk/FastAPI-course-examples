import sqlite3

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr

app = FastAPI(title="Contact Book API")

DB_NAME = "contact.db"
connection = sqlite3.connect(DB_NAME)
cursor = connection.cursor()
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS contact (
        id INTEGER PRIMARY KEY,
        name VARCHAR(50),
        phone VARCHAR(50),
        email VARCHAR(50)
    )
    """
)
connection.commit()


class Contact(BaseModel):
    id: int
    name: str
    phone: str
    email: EmailStr


class ContactCreate(BaseModel):
    name: str
    phone: str
    email: EmailStr


@app.get("/")
def read_root():
    return {"message": "Welcome to Contact Book API"}


@app.get("/contacts/")
def get_contacts() -> list[Contact]:
    with sqlite3.Connection(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contact")
        rows = cursor.fetchall()

    return [Contact(id=row[0], name=row[1], phone=row[2], email=row[3]) for row in rows]


@app.post("/contacts/")
def add_contact(contact: ContactCreate) -> Contact:
    with sqlite3.Connection(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM contact WHERE email = ?", (contact.email,))
        row = cursor.fetchone()

        if row is not None:
            raise HTTPException(
                status_code=400, detail="Contact with this email already exists."
            )

        cursor = cursor.execute(
            "INSERT INTO contact (name, phone, email) VALUES (?, ?, ?) RETURNING id",
            (
                contact.name,
                contact.phone,
                contact.email,
            ),
        )
        contact_id = cursor.fetchone()[0]
        conn.commit()

    return Contact(
        id=contact_id,
        name=contact.name,
        phone=contact.phone,
        email=contact.email,
    )
