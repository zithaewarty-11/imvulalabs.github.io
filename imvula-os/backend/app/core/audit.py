from sqlalchemy.orm import Session

from app.models.audit import AuditEvent


def record_audit(
    db: Session,
    *,
    org_id: int,
    actor_id: int,
    action: str,
    target_type: str,
    target_id: int,
    details: str = "",
) -> AuditEvent:
    """Add an audit event to the session (caller commits)."""
    event = AuditEvent(
        org_id=org_id,
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
    )
    db.add(event)
    return event
