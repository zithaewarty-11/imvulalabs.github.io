from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_register_returns_token_and_user_is_owner():
    r = client.post("/auth/register", json={
        "email": "alice@example.com",
        "password": "password123",
        "organisation_name": "Acme Co",
    })
    assert r.status_code == 201, r.text
    token = r.json()["access_token"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    data = me.json()
    assert data["email"] == "alice@example.com"
    assert data["role"] == "owner"
    assert data["org_id"] > 0


def test_duplicate_email_rejected():
    body = {
        "email": "dup@example.com",
        "password": "password123",
        "organisation_name": "Dup Co",
    }
    assert client.post("/auth/register", json=body).status_code == 201
    assert client.post("/auth/register", json=body).status_code == 400


def test_login_wrong_password_rejected():
    client.post("/auth/register", json={
        "email": "bob@example.com",
        "password": "password123",
        "organisation_name": "Bob Co",
    })
    r = client.post("/auth/login", json={
        "email": "bob@example.com",
        "password": "wrong-password",
    })
    assert r.status_code == 401


def test_login_correct_password_works():
    client.post("/auth/register", json={
        "email": "carol@example.com",
        "password": "password123",
        "organisation_name": "Carol Co",
    })
    r = client.post("/auth/login", json={
        "email": "carol@example.com",
        "password": "password123",
    })
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_me_without_token_rejected():
    r = client.get("/auth/me")
    assert r.status_code == 422


def test_me_with_bad_token_rejected():
    r = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert r.status_code == 401


def test_two_organisations_are_isolated():
    a = client.post("/auth/register", json={
        "email": "orgA@example.com",
        "password": "password123",
        "organisation_name": "Organisation A",
    }).json()
    b = client.post("/auth/register", json={
        "email": "orgB@example.com",
        "password": "password123",
        "organisation_name": "Organisation B",
    }).json()

    me_a = client.get("/auth/me", headers={"Authorization": f"Bearer {a['access_token']}"}).json()
    me_b = client.get("/auth/me", headers={"Authorization": f"Bearer {b['access_token']}"}).json()

    assert me_a["org_id"] != me_b["org_id"]
