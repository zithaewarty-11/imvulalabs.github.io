from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def _register(email, org):
    r = client.post("/auth/register", json={"email": email, "password": "password123", "organisation_name": org})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}

def test_create_asset_with_owner_and_category():
    h = _register("adv1@test.com", "Adv Org 1")
    # Get the user ID
    me = client.get("/auth/me", headers=h).json()
    
    r = client.post("/quantum/assets", json={
        "name": "Main Database",
        "asset_type": "database",
        "category": "data",
        "criticality": "critical",
        "owner_id": me["id"]
    }, headers=h)
    assert r.status_code == 201
    assert r.json()["category"] == "data"
    assert r.json()["owner_id"] == me["id"]

def test_update_asset_owner():
    h = _register("adv2@test.com", "Adv Org 2")
    asset = client.post("/quantum/assets", json={"name": "Server", "asset_type": "server"}, headers=h).json()
    
    r = client.patch(f"/quantum/assets/{asset['id']}", json={"category": "infrastructure", "criticality": "high"}, headers=h)
    assert r.status_code == 200
    assert r.json()["category"] == "infrastructure"

def test_list_org_users():
    h = _register("adv3@test.com", "Adv Org 3")
    r = client.get("/auth/users", headers=h)
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["email"] == "adv3@test.com"

def test_asset_history_endpoint():
    h = _register("adv4@test.com", "Adv Org 4")
    asset = client.post("/quantum/assets", json={"name": "Web App", "asset_type": "website"}, headers=h).json()
    
    # Generate a history event by updating it
    client.patch(f"/quantum/assets/{asset['id']}", json={"criticality": "high"}, headers=h)
    
    r = client.get(f"/quantum/assets/{asset['id']}/history", headers=h)
    assert r.status_code == 200
    assert len(r.json()) >= 1
