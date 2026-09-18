import pytest

from app import create_app, db


@pytest.fixture()
def client(tmp_path):
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret",
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.sqlite3'}",
        "WTF_CSRF_ENABLED": False,
    })
    with app.app_context():
        db.drop_all()
        db.create_all()
    with app.test_client() as test_client:
        yield test_client


def csrf(client):
    return client.get("/api/auth/csrf").get_json()["csrf_token"]


def register(client, email="teacher@example.com"):
    token = csrf(client)
    return client.post(
        "/api/auth/register",
        json={"name": "Teacher", "email": email, "password": "correct horse battery staple"},
        headers={"X-CSRF-Token": token},
    )


def student_payload(student_id="101"):
    return {
        "id": student_id,
        "name": "Asha Singh",
        "age": 18,
        "course": "Computer Science",
        "attendance": 92,
        "marks": {"Math": 85, "Science": 82, "English": 88},
    }


def test_registration_login_and_student_ownership(client):
    response = register(client)
    assert response.status_code == 201
    token = csrf(client)
    created = client.post("/api/students", json=student_payload(), headers={"X-CSRF-Token": token})
    assert created.status_code == 201
    assert created.get_json()["grade"] == "B"
    listed = client.get("/api/students")
    assert listed.status_code == 200
    assert listed.get_json()["students"]["101"]["attendance"] == 92


def test_mutations_require_csrf(client):
    register(client)
    response = client.post("/api/students", json=student_payload())
    assert response.status_code == 403


def test_invalid_student_is_rejected(client):
    register(client)
    response = client.post(
        "/api/students",
        json={**student_payload(), "attendance": 140},
        headers={"X-CSRF-Token": csrf(client)},
    )
    assert response.status_code == 400


def test_users_cannot_access_each_others_students(client):
    register(client, "first@example.com")
    client.post("/api/students", json=student_payload(), headers={"X-CSRF-Token": csrf(client)})
    client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf(client)})
    register(client, "second@example.com")
    assert client.get("/api/students").get_json()["students"] == {}


def test_follow_up_status_is_persisted(client):
    register(client)
    token = csrf(client)
    client.post("/api/students", json={**student_payload(), "attendance": 64}, headers={"X-CSRF-Token": token})
    response = client.post("/api/students/101/follow-up", headers={"X-CSRF-Token": csrf(client)})
    assert response.status_code == 200
    assert response.get_json()["followed_up"] is True
    assert client.get("/api/students").get_json()["students"]["101"]["followed_up"] is True
