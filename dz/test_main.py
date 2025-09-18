from fastapi.testclient import TestClient

from .main import app

client = TestClient(app)


def test_send_email():
    response = client.post(
        "/send-email/",
        data={"email": "ukr.vadya@gmail.com", "subject": "IMG", "body": "IMG"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Запит на відправлення листа прийнято"


def test_upload_file(tmp_path):
    file_path = tmp_path / "test.png"
    with open(file_path, "wb") as f:
        f.write(b"")

    with open(file_path, "rb") as f:
        response = client.post(
            "/upload-file/", files={"file": ("test.png", f, "image/png")}
        )
    assert response.status_code == 200
    assert "Файл test.png завантажено" in response.json()["message"]
