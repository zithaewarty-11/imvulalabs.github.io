from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.user import User

client = TestClient(app)

def _register(email, org):
    r = client.post("/auth/register", json={
        "email": email, "password": "password123", "organisation_name": org
    })
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}

def _set_role(email, role):
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == email).first()
        u.role = role
        db.commit()
    finally:
        db.close()

def test_create_and_list_assessment():
    h = _register("assess1@test.com", "Assess Org 1")
    r = client.post("/assessments", json={
        "name": "Q1 Web App Test",
        "target": "https://example.com",
        "assessment_type": "web_app",
        "scope": "Login and checkout",
        "authorisation_proof": "Signed letter from CEO dated 2026-01-01"
    }, headers=h)
    assert r.status_code == 201, r.text
    a = r.json()
    assert a["name"] == "Q1 Web App Test"
    assert a["status"] == "pending"

    lst = client.get("/assessments", headers=h).json()
    assert len(lst) == 1

def test_invalid_assessment_type():
    h = _register("assess2@test.com", "Assess Org 2")
    r = client.post("/assessments", json={
        "name": "Bad Type",
        "target": "https://example.com",
        "assessment_type": "hacking",
        "authorisation_proof": "Signed letter from CEO"
    }, headers=h)
    assert r.status_code == 422 # Pydantic rejects invalid regex

def test_assessments_isolated_between_orgs():
    h1 = _register("assess3@test.com", "Assess Org 3")
    h2 = _register("assess4@test.com", "Assess Org 4")
    
    client.post("/assessments", json={
        "name": "Secret", "target": "https://secret.com",
        "assessment_type": "api",
        "authorisation_proof": "Written authorisation on file"
    }, headers=h1)

    lst1 = client.get("/assessments", headers=h1).json()
    lst2 = client.get("/assessments", headers=h2).json()
    assert len(lst1) == 1
    assert len(lst2) == 0

    # Org 2 tries to view Org 1's assessment
    r = client.get(f"/assessments/{lst1[0]['id']}", headers=h2)
    assert r.status_code == 404

def test_member_cannot_update_status():
    h = _register("assess5@test.com", "Assess Org 5")
    a = client.post("/assessments", json={
        "name": "Test Assessment", "target": "https://t.com", "assessment_type": "vulnerability",
        "authorisation_proof": "Authorised by management"
    }, headers=h).json()

    _set_role("assess5@test.com", "member")

    r = client.patch(f"/assessments/{a['id']}", json={"status": "completed"}, headers=h)
    assert r.status_code == 403 # Forbidden

def test_findings_are_org_scoped():
    h1 = _register("assess6@test.com", "Assess Org 6")
    h2 = _register("assess7@test.com", "Assess Org 7")
    a = client.post("/assessments", json={
        "name": "Test Assessment", "target": "https://t.com", "assessment_type": "web_app",
        "authorisation_proof": "Authorised by management"
    }, headers=h1).json()

    # Org 2 tries to add a finding to Org 1's assessment
    r = client.post(f"/assessments/{a['id']}/findings", json={
        "title": "SQLi", "severity": "critical", "remediation": "Use parameterised queries"
    }, headers=h2)
    assert r.status_code == 404
