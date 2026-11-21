from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _register(email: str, org: str) -> dict:
    r = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "password123",
            "organisation_name": org,
        },
    )
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_create_and_list_asset():
    h = _register("a1@test.com", "Org A1")
    r = client.post(
        "/quantum/assets",
        json={
            "name": "Company website",
            "asset_type": "website",
            "criticality": "high",
            "description": "Public marketing site",
        },
        headers=h,
    )
    assert r.status_code == 201, r.text
    asset = r.json()
    assert asset["name"] == "Company website"
    assert asset["org_id"] > 0

    lst = client.get("/quantum/assets", headers=h).json()
    assert len(lst) == 1
    assert lst[0]["id"] == asset["id"]


def test_invalid_asset_type_rejected():
    h = _register("a2@test.com", "Org A2")
    r = client.post(
        "/quantum/assets",
        json={"name": "Bad", "asset_type": "spaceship", "criticality": "low"},
        headers=h,
    )
    assert r.status_code == 422


def test_assets_isolated_between_orgs():
    h1 = _register("iso1@test.com", "Iso Org 1")
    h2 = _register("iso2@test.com", "Iso Org 2")

    client.post(
        "/quantum/assets",
        json={"name": "Secret A1", "asset_type": "server"},
        headers=h1,
    )

    lst1 = client.get("/quantum/assets", headers=h1).json()
    lst2 = client.get("/quantum/assets", headers=h2).json()
    assert len(lst1) == 1
    assert len(lst2) == 0

    r = client.get(f"/quantum/assets/{lst1[0]['id']}", headers=h2)
    assert r.status_code == 404


def test_cross_org_delete_blocked():
    h1 = _register("del1@test.com", "Del Org 1")
    h2 = _register("del2@test.com", "Del Org 2")
    asset = client.post(
        "/quantum/assets",
        json={"name": "X", "asset_type": "email"},
        headers=h1,
    ).json()
    r = client.delete(f"/quantum/assets/{asset['id']}", headers=h2)
    assert r.status_code == 404
    assert client.get(f"/quantum/assets/{asset['id']}", headers=h1).status_code == 200


def test_risk_requires_own_asset():
    h1 = _register("r1@test.com", "R Org 1")
    h2 = _register("r2@test.com", "R Org 2")
    asset_h1 = client.post(
        "/quantum/assets",
        json={"name": "H1 Asset", "asset_type": "server"},
        headers=h1,
    ).json()

    r = client.post(
        "/quantum/risks",
        json={"asset_id": asset_h1["id"], "title": "Steal", "severity": "high"},
        headers=h2,
    )
    assert r.status_code == 404


def test_cannot_delete_asset_with_risks():
    h = _register("del@test.com", "Del Org")
    asset = client.post(
        "/quantum/assets",
        json={"name": "Srv", "asset_type": "server"},
        headers=h,
    ).json()
    client.post(
        "/quantum/risks",
        json={"asset_id": asset["id"], "title": "R", "severity": "high"},
        headers=h,
    )
    r = client.delete(f"/quantum/assets/{asset['id']}", headers=h)
    assert r.status_code == 409


def test_full_risk_remediation_flow():
    h = _register("flow@test.com", "Flow Org")
    asset = client.post(
        "/quantum/assets",
        json={"name": "DB", "asset_type": "database", "criticality": "critical"},
        headers=h,
    ).json()

    risk = client.post(
        "/quantum/risks",
        json={
            "asset_id": asset["id"],
            "title": "Weak password policy",
            "description": "Admin account uses an 8-char password",
            "severity": "high",
        },
        headers=h,
    ).json()
    assert risk["status"] == "open"

    r = client.patch(
        f"/quantum/risks/{risk['id']}",
        json={"status": "in_progress"},
        headers=h,
    )
    assert r.status_code == 200 and r.json()["status"] == "in_progress"

    r = client.patch(
        f"/quantum/risks/{risk['id']}", json={"status": "banana"}, headers=h
    )
    assert r.status_code == 422

    rem = client.post(
        "/quantum/remediations",
        json={"risk_id": risk["id"], "description": "Enable 12-char minimum + MFA"},
        headers=h,
    ).json()
    assert rem["status"] == "pending"

    r = client.patch(
        f"/quantum/remediations/{rem['id']}", json={"status": "done"}, headers=h
    )
    assert r.status_code == 200 and r.json()["status"] == "done"

    lst = client.get(f"/quantum/risks/{risk['id']}/remediations", headers=h).json()
    assert len(lst) == 1


def test_filter_risks_by_severity():
    h = _register("filt@test.com", "Filter Org")
    asset = client.post(
        "/quantum/assets",
        json={"name": "Srv", "asset_type": "server"},
        headers=h,
    ).json()
    client.post(
        "/quantum/risks",
        json={"asset_id": asset["id"], "title": "L", "severity": "low"},
        headers=h,
    )
    client.post(
        "/quantum/risks",
        json={"asset_id": asset["id"], "title": "H", "severity": "high"},
        headers=h,
    )

    highs = client.get("/quantum/risks?severity=high", headers=h).json()
    assert len(highs) == 1
    assert highs[0]["severity"] == "high"


def test_quantum_endpoints_require_auth():
    assert client.get("/quantum/assets").status_code == 422
    assert (
        client.post(
            "/quantum/assets", json={"name": "x", "asset_type": "email"}
        ).status_code
        == 422
    )
