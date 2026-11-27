from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def _register(email, org):
    r = client.post("/auth/register", json={"email": email, "password": "password123", "organisation_name": org})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}

def test_create_risk_with_assignee_and_evidence():
    h = _register("vuln1@test.com", "Vuln Org 1")
    me = client.get("/auth/me", headers=h).json()
    asset = client.post("/quantum/assets", json={"name": "Web App", "asset_type": "website"}, headers=h).json()

    r = client.post("/quantum/risks", json={
        "asset_id": asset["id"], "title": "SQL Injection", "severity": "critical",
        "assignee_id": me["id"], "evidence": "https://pastebin.com/xyz", "remediation_notes": "Use parameterised queries"
    }, headers=h)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["assignee_id"] == me["id"]
    assert data["evidence"] == "https://pastebin.com/xyz"

def test_update_risk_evidence_and_status():
    h = _register("vuln2@test.com", "Vuln Org 2")
    asset = client.post("/quantum/assets", json={"name": "API", "asset_type": "server"}, headers=h).json()
    risk = client.post("/quantum/risks", json={"asset_id": asset["id"], "title": "XSS", "severity": "high"}, headers=h).json()

    r = client.patch(f"/quantum/risks/{risk['id']}", json={
        "status": "in_progress", "evidence": "Screenshot attached", "remediation_notes": "Sanitize output"
    }, headers=h)
    assert r.status_code == 200
    assert r.json()["status"] == "in_progress"
    assert r.json()["evidence"] == "Screenshot attached"

def test_risk_history_records_changes():
    h = _register("vuln3@test.com", "Vuln Org 3")
    asset = client.post("/quantum/assets", json={"name": "DB", "asset_type": "database"}, headers=h).json()
    risk = client.post("/quantum/risks", json={"asset_id": asset["id"], "title": "Weak Password", "severity": "medium"}, headers=h).json()

    client.patch(f"/quantum/risks/{risk['id']}", json={"status": "resolved"}, headers=h)

    r = client.get(f"/quantum/risks/{risk['id']}/history", headers=h)
    assert r.status_code == 200
    actions = [e["action"] for e in r.json()]
    assert "risk.created" in actions
    assert "risk.updated" in actions

def test_risk_history_isolated_between_orgs():
    h1 = _register("vuln4@test.com", "Vuln Org 4")
    h2 = _register("vuln5@test.com", "Vuln Org 5")
    asset = client.post("/quantum/assets", json={"name": "App", "asset_type": "website"}, headers=h1).json()
    risk = client.post("/quantum/risks", json={"asset_id": asset["id"], "title": "Test", "severity": "low"}, headers=h1).json()

    r = client.get(f"/quantum/risks/{risk['id']}/history", headers=h2)
    assert r.status_code == 404
