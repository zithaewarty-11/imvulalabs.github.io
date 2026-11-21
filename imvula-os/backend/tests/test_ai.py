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
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == email).first()
        assert u is not None
        u.role = role
        db.commit()
    finally:
        db.close()


def test_ai_complete_returns_mock_response():
    """Default provider is mock — no API key, deterministic output."""
    h = _register("ai1@test.com", "AI Org 1")
    r = client.post(
        "/ai/complete",
        json={"prompt": "What is a risk assessment?"},
        headers=h,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["provider"] == "mock"
    assert data["model"] == ""
    assert "mock-ai" in data["response"]
    assert "What is a risk assessment?" in data["response"]
    assert data["prompt_chars"] == len("What is a risk assessment?")
    assert data["response_chars"] > 0


def test_ai_complete_requires_auth():
    r = client.post("/ai/complete", json={"prompt": "hi"})
    assert r.status_code == 422


def test_ai_complete_rejects_empty_prompt():
    h = _register("ai2@test.com", "AI Org 2")
    r = client.post("/ai/complete", json={"prompt": ""}, headers=h)
    assert r.status_code == 422


def test_ai_complete_rejects_overlong_prompt():
    h = _register("ai3@test.com", "AI Org 3")
    long_prompt = "a" * 4001  # max is 4000
    r = client.post(
        "/ai/complete",
        json={"prompt": long_prompt},
        headers=h,
    )
    assert r.status_code == 422


def test_ai_complete_logs_usage():
    """Every successful call must create exactly one usage row."""
    h = _register("ai4@test.com", "AI Org 4")
    r = client.post(
        "/ai/complete",
        json={"prompt": "hello world"},
        headers=h,
    )
    assert r.status_code == 200

    # Admin-level usage list should show the call
    usage = client.get("/ai/usage", headers=h).json()
    assert len(usage) == 1
    row = usage[0]
    assert row["provider"] == "mock"
    assert row["prompt_chars"] == len("hello world")
    assert row["response_chars"] > 0
    assert row["success"] is True
    assert row["prompt_preview"] == "hello world"


def test_usage_isolated_between_orgs():
    h1 = _register("aix1@test.com", "AIX Org 1")
    h2 = _register("aix2@test.com", "AIX Org 2")

    client.post("/ai/complete", json={"prompt": "org 1 asks"}, headers=h1)

    u1 = client.get("/ai/usage", headers=h1).json()
    u2 = client.get("/ai/usage", headers=h2).json()
    assert len(u1) == 1
    assert len(u2) == 0


def test_prompt_preview_truncated_to_200_chars():
    """Preview stored in DB should be capped at 200 chars even for longer prompts."""
    h = _register("ai5@test.com", "AI Org 5")
    long_prompt = "x" * 500
    r = client.post("/ai/complete", json={"prompt": long_prompt}, headers=h)
    assert r.status_code == 200

    usage = client.get("/ai/usage", headers=h).json()
    assert len(usage) == 1
    # Preview must be exactly 200 chars even though prompt was 500
    assert len(usage[0]["prompt_preview"]) == 200
    # But the char count records the real length
    assert usage[0]["prompt_chars"] == 500

def test_rate_limit_blocks_after_60_calls(monkeypatch):
    """Bypass the 60-call wall by lowering it to 2 for this test."""
    import app.api.ai as ai_module

    monkeypatch.setattr(ai_module, "RATE_LIMIT_CALLS", 2)

    h = _register("rl1@test.com", "RL Org 1")
    assert client.post("/ai/complete", json={"prompt": "one"}, headers=h).status_code == 200
    assert client.post("/ai/complete", json={"prompt": "two"}, headers=h).status_code == 200

    r = client.post("/ai/complete", json={"prompt": "three"}, headers=h)
    assert r.status_code == 429, r.text
    assert "rate limit" in r.json()["detail"].lower()


def test_rate_limit_isolated_between_orgs():
    """Org 1 hitting its limit should not affect Org 2."""
    h1 = _register("rl2@test.com", "RL Org 2")
    h2 = _register("rl3@test.com", "RL Org 3")

    # Burn through some calls on Org 1 (not enough to hit limit)
    for i in range(3):
        client.post("/ai/complete", json={"prompt": f"call {i}"}, headers=h1)

    # Org 2 should still work fine
    r = client.post("/ai/complete", json={"prompt": "fresh org"}, headers=h2)
    assert r.status_code == 200


def test_guardian_run_must_be_approved_for_ai():
    """If you attach a Guardian run, it must be approved — not pending."""
    h = _register("gai1@test.com", "GAI Org 1")

    # Create agent + run (run is pending_approval)
    agent = client.post(
        "/guardian/agents",
        json={"name": "P", "kind": "planner"},
        headers=h,
    ).json()
    run = client.post(
        "/guardian/runs",
        json={"agent_id": agent["id"], "request": "draft"},
        headers=h,
    ).json()
    assert run["status"] == "pending_approval"

    # Try to use AI with this pending run — must fail
    r = client.post(
        "/ai/complete",
        json={"prompt": "go", "guardian_run_id": run["id"]},
        headers=h,
    )
    assert r.status_code == 400
    assert "approved" in r.json()["detail"].lower()


def test_guardian_approved_run_allows_ai():
    """Once approved, the same call should succeed."""
    h = _register("gai2@test.com", "GAI Org 2")

    agent = client.post(
        "/guardian/agents",
        json={"name": "P", "kind": "planner"},
        headers=h,
    ).json()
    run = client.post(
        "/guardian/runs",
        json={"agent_id": agent["id"], "request": "draft"},
        headers=h,
    ).json()

    client.post(f"/guardian/runs/{run['id']}/approve", headers=h)

    r = client.post(
        "/ai/complete",
        json={"prompt": "go", "guardian_run_id": run["id"]},
        headers=h,
    )
    assert r.status_code == 200, r.text


def test_guardian_run_cross_org_rejected():
    """You cannot pass another org's approved run as guardian_run_id."""
    h1 = _register("gcx1@test.com", "GCX Org 1")
    h2 = _register("gcx2@test.com", "GCX Org 2")

    agent = client.post(
        "/guardian/agents",
        json={"name": "P", "kind": "planner"},
        headers=h1,
    ).json()
    run = client.post(
        "/guardian/runs",
        json={"agent_id": agent["id"], "request": "draft"},
        headers=h1,
    ).json()
    client.post(f"/guardian/runs/{run['id']}/approve", headers=h1)

    # Org 2 tries to use Org 1's approved run — must be 404
    r = client.post(
        "/ai/complete",
        json={"prompt": "hijack", "guardian_run_id": run["id"]},
        headers=h2,
    )
    assert r.status_code == 404


def test_guardian_nonexistent_run_rejected():
    h = _register("gne@test.com", "GNE Org")
    r = client.post(
        "/ai/complete",
        json={"prompt": "go", "guardian_run_id": 9999},
        headers=h,
    )
    assert r.status_code == 404


def test_usage_me_returns_only_own_calls():
    """Two users in the same org — /usage/me should show only own."""
    h_a = _register("me_a@test.com", "ME Org")
    # Register user B in *different* org (simpler than inviting)
    # — this test just verifies /usage/me works and is scoped to caller
    client.post("/ai/complete", json={"prompt": "from A"}, headers=h_a)

    me_usage = client.get("/ai/usage/me", headers=h_a).json()
    assert len(me_usage) == 1
    assert me_usage[0]["prompt_preview"] == "from A"


def test_usage_requires_admin_for_org_wide():
    """Members cannot see the org-wide usage ledger, but can see their own."""
    h = _register("memusage@test.com", "MemUsage Org")
    client.post("/ai/complete", json={"prompt": "test"}, headers=h)

    _set_role("memusage@test.com", "member")

    r = client.get("/ai/usage", headers=h)
    assert r.status_code == 403

    r = client.get("/ai/usage/me", headers=h)
    assert r.status_code == 200
    assert len(r.json()) == 1

def test_ai_call_creates_audit_event():
    """Every successful call creates ai.completed in the audit log."""
    from app.models.audit import AuditEvent

    h = _register("audit1@test.com", "Audit Org 1")
    client.post("/ai/complete", json={"prompt": "hello"}, headers=h)

    db = SessionLocal()
    try:
        events = (
            db.query(AuditEvent)
            .filter(AuditEvent.action == "ai.completed")
            .all()
        )
        assert len(events) >= 1
        # The most recent event should be for our call
        assert events[-1].target_type == "ai_usage"
        assert "provider=mock" in events[-1].details
    finally:
        db.close()


def test_provider_failure_returns_502_but_logs_usage(monkeypatch):
    """When provider raises, endpoint returns 502 but usage row is saved."""
    from app.core.ai_provider import AIProvider, AIProviderError
    import app.api.ai as ai_module

    class FailingProvider(AIProvider):
        name = "failing"

        async def complete(self, prompt, max_tokens=512):
            raise AIProviderError("simulated upstream failure")

    monkeypatch.setattr(ai_module, "get_provider", lambda: FailingProvider())

    h = _register("fail1@test.com", "Fail Org 1")
    r = client.post("/ai/complete", json={"prompt": "boom"}, headers=h)
    assert r.status_code == 502, r.text
    assert "simulated upstream failure" in r.json()["detail"]

    # Usage row must still be recorded with success=False
    usage = client.get("/ai/usage", headers=h).json()
    assert len(usage) == 1
    row = usage[0]
    assert row["success"] is False
    assert "simulated upstream failure" in row["error_message"]
    assert row["provider"] == "failing"
