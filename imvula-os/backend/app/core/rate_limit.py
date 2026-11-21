"""
Per-organisation rate limiting for AI calls.

Strategy: count rows in ai_usage for this org within the last N minutes.
Simple, no extra infrastructure, survives restarts, works with SQLite.

For scale (10k+ orgs), swap this for Redis or a token-bucket service.
"""
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.ai_usage import AIUsage


def enforce_rate_limit(
    db: Session,
    org_id: int,
    *,
    max_calls: int,
    window_minutes: int,
) -> None:
    """Raise 429 if the org has exceeded max_calls in the last window_minutes."""
    window_start = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(
        minutes=window_minutes
    )
    count = (
        db.query(AIUsage)
        .filter(
            AIUsage.org_id == org_id,
            AIUsage.created_at >= window_start,
        )
        .count()
    )
    if count >= max_calls:
        raise HTTPException(
            status_code=429,
            detail=(
                f"AI rate limit reached: {count}/{max_calls} calls "
                f"in the last {window_minutes} minutes. Try again later."
            ),
        )
