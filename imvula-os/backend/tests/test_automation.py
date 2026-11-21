from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models.user import User

client = TestClient(app)


def _register(email: str, org: str) -> dict:
    r = client.post(
        "/auth/register",
        json={"email": email, "password": "password123", "organisation_name": org},
    )
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _set_role(email: str, role: str) -> None:
    """Change a user's role in DB. Tokens stay valid; role is read from DB per request."""
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == email).first()
        assert u is not None
        u.role = role
        db.commit()
    finally:
        db.close()


def test_create_and_list_task():
    h = _register("t1@test.com", "Task Org 1")
    r = client.post(
        "/automation/tasks",
        json={"title": "Update firewall rules", "priority": "high"},
        headers=h,
    )
    assert r.status_code == 201, r.text
    task = r.json()
    assert task["title"] == "Update firewall rules"
    assert task["status"] == "todo"
    assert task["priority"] == "high"

    lst = client.get("/automation/tasks", headers=h).json()
    assert len(lst) == 1
    assert lst[0]["id"] == task["id"]


def test_invalid_priority_rejected():
    h = _register("t2@test.com", "Task Org 2")
    r = client.post(
        "/automation/tasks",
        json={"title": "X", "priority": "urgent"},
        headers=h,
    )
    assert r.status_code == 422


def test_tasks_isolated_between_orgs():
    h1 = _register("ti1@test.com", "TI Org 1")
    h2 = _register("ti2@test.com", "TI Org 2")
    client.post("/automation/tasks", json={"title": "Secret"}, headers=h1)

    lst1 = client.get("/automation/tasks", headers=h1).json()
    lst2 = client.get("/automation/tasks", headers=h2).json()
    assert len(lst1) == 1
    assert len(lst2) == 0

    r = client.get(f"/automation/tasks/{lst1[0]['id']}", headers=h2)
    assert r.status_code == 404


def test_update_task_status():
    h = _register("tu@test.com", "TU Org")
    task = client.post(
        "/automation/tasks", json={"title": "Do the thing"}, headers=h
    ).json()
    assert task["status"] == "todo"

    r = client.patch(
        f"/automation/tasks/{task['id']}",
        json={"status": "in_progress"},
        headers=h,
    )
    assert r.status_code == 200
    assert r.json()["status"] == "in_progress"

    r = client.patch(
        f"/automation/tasks/{task['id']}",
        json={"status": "banana"},
        headers=h,
    )
    assert r.status_code == 422


def test_filter_by_priority():
    h = _register("tf@test.com", "TF Org")
    client.post(
        "/automation/tasks",
        json={"title": "A", "priority": "high"},
        headers=h,
    )
    client.post(
        "/automation/tasks",
        json={"title": "B", "priority": "low"},
        headers=h,
    )

    highs = client.get("/automation/tasks?priority=high", headers=h).json()
    assert len(highs) == 1
    assert highs[0]["priority"] == "high"


def test_cross_org_update_blocked():
    h1 = _register("cu1@test.com", "CU Org 1")
    h2 = _register("cu2@test.com", "CU Org 2")
    task = client.post(
        "/automation/tasks", json={"title": "Owned"}, headers=h1
    ).json()

    r = client.patch(
        f"/automation/tasks/{task['id']}",
        json={"status": "done"},
        headers=h2,
    )
    assert r.status_code == 404


def test_owner_can_delete_task():
    h = _register("tdel@test.com", "TDEL Org")
    task = client.post(
        "/automation/tasks", json={"title": "Deletable"}, headers=h
    ).json()

    r = client.delete(f"/automation/tasks/{task['id']}", headers=h)
    assert r.status_code == 204


def test_member_cannot_delete_but_can_create():
    h = _register("mem@test.com", "MEM Org")
    task = client.post(
        "/automation/tasks", json={"title": "Existing"}, headers=h
    ).json()

    _set_role("mem@test.com", "member")

    r = client.delete(f"/automation/tasks/{task['id']}", headers=h)
    assert r.status_code == 403

    r = client.post(
        "/automation/tasks", json={"title": "New from member"}, headers=h
    )
    assert r.status_code == 201


def test_member_cannot_delete_quantum_asset():
    h = _register("memq@test.com", "MEMQ Org")
    asset = client.post(
        "/quantum/assets",
        json={"name": "Web", "asset_type": "website"},
        headers=h,
    ).json()

    _set_role("memq@test.com", "member")

    r = client.delete(f"/quantum/assets/{asset['id']}", headers=h)
    assert r.status_code == 403


def test_endpoints_require_auth():
    assert client.get("/automation/tasks").status_code == 422
    assert (
        client.post("/automation/tasks", json={"title": "x"}).status_code
        == 422
    )
