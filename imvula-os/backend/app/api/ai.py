from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.ai_provider import AIProviderError, get_provider
from app.core.audit import record_audit
from app.core.database import get_db
from app.core.permissions import require_admin
from app.core.rate_limit import enforce_rate_limit
from app.deps import get_current_user
from app.models.ai_usage import AIUsage
from app.models.guardian import AgentRun
from app.models.user import User
from app.schemas.ai import AICompleteRequest, AICompleteResponse, AIUsageOut

router = APIRouter(prefix="/ai", tags=["ai"])

# Per-org rate limit: 60 calls per hour by default.
# Override by editing these constants (or move into settings later).
RATE_LIMIT_CALLS = 60
RATE_LIMIT_WINDOW_MINUTES = 60


@router.post("/complete", response_model=AICompleteResponse)
async def complete(
    body: AICompleteRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # 1. Rate limit check
    enforce_rate_limit(
        db,
        user.org_id,
        max_calls=RATE_LIMIT_CALLS,
        window_minutes=RATE_LIMIT_WINDOW_MINUTES,
    )

    # 2. If caller attached a Guardian run, it must be approved and in-org
    if body.guardian_run_id is not None:
        run = db.get(AgentRun, body.guardian_run_id)
        if run is None or run.org_id != user.org_id:
            raise HTTPException(status_code=404, detail="Guardian run not found")
        if run.status != "approved":
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Guardian run status is '{run.status}', must be "
                    f"'approved' before AI can run"
                ),
            )

    # 3. Call the provider
    provider = get_provider()
    prompt_preview = body.prompt[:200]
    response_text = ""
    success = True
    error_message = ""

    try:
        response_text = await provider.complete(body.prompt, body.max_tokens)
    except AIProviderError as e:
        success = False
        error_message = str(e)[:500]

    # 4. Log usage (always — success or fail)
    usage = AIUsage(
        org_id=user.org_id,
        user_id=user.id,
        provider=provider.name,
        model=getattr(provider, "model", ""),
        prompt_preview=prompt_preview,
        prompt_chars=len(body.prompt),
        response_chars=len(response_text),
        success=success,
        error_message=error_message,
    )
    db.add(usage)
    db.flush()

    # 5. Audit event
    record_audit(
        db,
        org_id=user.org_id,
        actor_id=user.id,
        action="ai.completed" if success else "ai.failed",
        target_type="ai_usage",
        target_id=usage.id,
        details=f"provider={provider.name}",
    )
    db.commit()

    # 6. If provider failed, surface it — but the usage record is already saved
    if not success:
        raise HTTPException(
            status_code=502,
            detail=f"AI provider error: {error_message}",
        )

    return AICompleteResponse(
        response=response_text,
        provider=provider.name,
        model=getattr(provider, "model", ""),
        prompt_chars=len(body.prompt),
        response_chars=len(response_text),
    )

@router.get("/usage", response_model=list[AIUsageOut])
def list_usage(
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Org-scoped usage log. Any member can see their org's AI activity."""
    require_admin(user)
    return (
        db.query(AIUsage)
        .filter(AIUsage.org_id == user.org_id)
        .order_by(AIUsage.id.desc())
        .limit(min(max(limit, 1), 200))
        .all()
    )


@router.get("/usage/me", response_model=list[AIUsageOut])
def list_my_usage(
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Personal usage log — only the caller's own calls."""
    return (
        db.query(AIUsage)
        .filter(
            AIUsage.org_id == user.org_id,
            AIUsage.user_id == user.id,
        )
        .order_by(AIUsage.id.desc())
        .limit(min(max(limit, 1), 200))
        .all()
    )
