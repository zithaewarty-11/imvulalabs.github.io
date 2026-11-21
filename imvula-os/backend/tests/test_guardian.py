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
    """Change a user's role in DB. Token stays valid; role is read from DB per request."""
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == email).first()
        assert u is not None
        u.role = role
        db.commit()
    finally:
        db.close()


def test_owner_can_create_agent():
    h = _register("g1@test.com", "G Org 1")
    r = client.post(
        "/guardian/agents",
        json={"name": "Risk Analyser", "kind": "analyst", "description": "Reads risks"},
        headers=h,
    )
    assert r.status_code == 201, r.text
    agent = r.json()
    assert agent["name"] == "Risk Analyser"
    assert agent["kind"] == "analyst"
    assert agent["active"] is True
    assert agent["org_id"] > 0

    lst = client.get("/guardian/agents", headers=h).json()
    assert len(lst) == 1
    assert lst[0]["id"] == agent["id"]


def test_invalid_agent_kind_rejected():
    h = _register("g2@test.com", "G Org 2")
    r = client.post(
        "/guardian/agents",
        json={"name": "Bad", "kind": "terminator"},
        headers=h,
    )
    assert r.status_code == 422


def test_member_cannot_create_agent():
    h = _register("g3@test.com", "G Org 3")
    _set_role("g3@test.com", "member")
    r = client.post(
        "/guardian/agents",
        json={"name": "Sneaky", "kind": "executor"},
        headers=h,
    )
    assert r.status_code == 403


def test_agents_isolated_between_orgs():
    h1 = _register("gi1@test.com", "GI Org 1")
    h2 = _register("gi2@test.com", "GI Org 2")
    agent = client.post(
        "/guardian/agents",
        json={"name": "Secret Agent", "kind": "analyst"},
        headers=h1,
    ).json()

    lst1 = client.get("/guardian/agents", headers=h1).json()
    lst2 = client.get("/guardian/agents", headers=h2).json()
    assert len(lst1) == 1
    assert len(lst2) == 0

    r = client.get(f"/guardian/agents/{agent['id']}", headers=h2)
    assert r.status_code == 404


def test_create_run_lands_in_pending_approval():
    h = _register("gr1@test.com", "GR Org 1")
    agent = client.post(
        "/guardian/agents",
        json={"name": "Planner", "kind": "planner"},
        headers=h,
    ).json()

    r = client.post(
        "/guardian/runs",
        json={"agent_id": agent["id"], "request": "Draft a remediation plan"},
        headers=h,
    )
    assert r.status_code == 201, r.text
    run = r.json()
    assert run["status"] == "pending_approval"
    assert run["agent_id"] == agent["id"]
    assert run["decided_by"] is None


def test_inactive_agent_cannot_run():
    h = _register("gr2@test.com", "GR Org 2")
    agent = client.post(
        "/guardian/agents",
        json={"name": "Sleeper", "kind": "analyst"},
        headers=h,
    ).json()

    r = client.patch(
        f"/guardian/agents/{agent['id']}",
        json={"active": False},
        headers=h,
    )
    assert r.status_code == 200

    r = client.post(
        "/guardian/runs",
        json={"agent_id": agent["id"], "request": "Wake up"},
        headers=h,
    )
    assert r.status_code == 400


def test_cannot_create_run_against_other_org_agent():
    h1 = _register("grx1@test.com", "GRX Org 1")
    h2 = _register("grx2@test.com", "GRX Org 2")
    agent = client.post(
        "/guardian/agents",
        json={"name": "Owner's agent", "kind": "analyst"},
        headers=h1,
    ).json()

    r = client.post(
        "/guardian/runs",
        json={"agent_id": agent["id"], "request": "Use their agent"},
        headers=h2,
    )
    assert r.status_code == 404

def test_admin_approve_run():
    h = _register("ga1@test.com", "GA Org 1")
    agent = client.post(
        "/guardian/agents",
        json={"name": "Planner", "kind": "planner"},
        headers=h,
    ).json()
    run = client.post(
        "/guardian/runs",
        json={"agent_id": agent["id"], "request": "Draft plan"},
        headers=h,
    ).json()
    assert run["status"] == "pending_approval"

    r = client.post(f"/guardian/runs/{run['id']}/approve", headers=h)
    assert r.status_code == 200, r.text
    approved = r.json()
    assert approved["status"] == "approved"
    assert approved["decided_by"] is not None
    assert approved["decided_at"] is not None


def test_member_cannot_approve_run():
    h = _register("ga2@test.com", "GA Org 2")
    agent = client.post(
        "/guardian/agents",
        json={"name": "P", "kind": "planner"},
        headers=h,
    ).json()
    run = client.post(
        "/guardian/runs",
        json={"agent_id": agent["id"], "request": "Do it"},
        headers=h,
    ).json()

    _set_role("ga2@test.com", "member")

    r = client.post(f"/guardian/runs/{run['id']}/approve", headers=h)
    assert r.status_code == 403


def test_cannot_approve_twice():
    h = _register("ga3@test.com", "GA Org 3")
    agent = client.post(
        "/guardian/agents",
        json={"name": "P", "kind": "planner"},
        headers=h,
    ).json()
    run = client.post(
        "/guardian/runs",
        json={"agent_id": agent["id"], "request": "Once"},
        headers=h,
    ).json()

    assert client.post(f"/guardian/runs/{run['id']}/approve", headers=h).status_code == 200
    # Second attempt must fail with 409
    r = client.post(f"/guardian/runs/{run['id']}/approve", headers=h)
    assert r.status_code == 409


def test_reject_run_with_reason():
    h = _register("gr3@test.com", "GR Org 3")
    agent = client.post(
        "/guardian/agents",
        json={"name": "P", "kind": "planner"},
        headers=h,
    ).json()
    run = client.post(
        "/guardian/runs",
        json={"agent_id": agent["id"], "request": "Risky action"},
        headers=h,
    ).json()

    r = client.post(
        f"/guardian/runs/{run['id']}/reject",
        json={"result": "Too risky without more context"},
        headers=h,
    )
    assert r.status_code == 200, r.text
    rej = r.json()
    assert rej["status"] == "rejected"
    assert rej["result"] == "Too risky without more context"
    assert rej["decided_by"] is not None


def test_cannot_reject_after_approval():
    h = _register("gr4@test.com", "GR Org 4")
    agent = client.post(
        "/guardian/agents",
        json={"name": "P", "kind": "planner"},
        headers=h,
    ).json()
    run = client.post(
        "/guardian/runs",
        json={"agent_id": agent["id"], "request": "X"},
        headers=h,
    ).json()

    client.post(f"/guardian/runs/{run['id']}/approve", headers=h)
    r = client.post(f"/guardian/runs/{run['id']}/reject", headers=h)
    assert r.status_code == 409


def test_complete_approved_run():
    h = _register("gc1@test.com", "GC Org 1")
    agent = client.post(
        "/guardian/agents",
        json={"name": "P", "kind": "executor"},
        headers=h,
    ).json()
    run = client.post(
        "/guardian/runs",
        json={"agent_id": agent["id"], "request": "Do work"},
        headers=h,
    ).json()

    client.post(f"/guardian/runs/{run['id']}/approve", headers=h)
    r = client.post(
        f"/guardian/runs/{run['id']}/complete",
        json={"result": "Done successfully"},
        headers=h,
    )
    assert r.status_code == 200, r.text
    done = r.json()
    assert done["status"] == "completed"
    assert done["result"] == "Done successfully"


def test_cannot_complete_pending_run():
    h = _register("gc2@test.com", "GC Org 2")
    agent = client.post(
        "/guardian/agents",
        json={"name": "P", "kind": "executor"},
        headers=h,
    ).json()
    run = client.post(
        "/guardian/runs",
        json={"agent_id": agent["id"], "request": "Not yet approved"},
        headers=h,
    ).json()

    r = client.post(f"/guardian/runs/{run['id']}/complete", headers=h)
    assert r.status_code == 409


def test_cross_org_cannot_approve():
    h1 = _register("gx1@test.com", "GX Org 1")
    h2 = _register("gx2@test.com", "GX Org 2")
    agent = client.post(
        "/guardian/agents",
        json={"name": "A", "kind": "planner"},
        headers=h1,
    ).json()
    run = client.post(
        "/guardian/runs",
        json={"agent_id": agent["id"], "request": "X"},
        headers=h1,
    ).json()

    # Org 2 admin tries to approve Org 1's run — must be invisible (404)
    r = client.post(f"/guardian/runs/{run['id']}/approve", headers=h2)
    assert r.status_code == 404


def test_filter_runs_by_status():
    h = _register("gf1@test.com", "GF Org 1")
    agent = client.post(
        "/guardian/agents",
        json={"name": "P", "kind": "planner"},
        headers=h,
    ).json()
    run_a = client.post(
        "/guardian/runs",
        json={"agent_id": agent["id"], "request": "A"},
        headers=h,
    ).json()
    client.post(
        "/guardian/runs",
        json={"agent_id": agent["id"], "request": "B"},
        headers=h,
    )
    client.post(f"/guardian/runs/{run_a['id']}/approve", headers=h)

    pending = client.get("/guardian/runs?status_filter=pending_approval", headers=h).json()
    approved = client.get("/guardian/runs?status_filter=approved", headers=h).json()
    assert len(pending) == 1
    assert len(approved) == 1
    assert approved[0]["id"] == run_a["id"]


def test_guardian_endpoints_require_auth():
    assert client.get("/guardian/agents").status_code == 422
    assert client.get("/guardian/runs").status_code == 422
