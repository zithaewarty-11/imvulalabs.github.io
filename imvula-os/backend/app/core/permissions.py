from fastapi import HTTPException

from app.models.user import User


def require_role(user: User, *roles: str) -> None:
    """Raise 403 if the user's role is not in the allowed list."""
    if user.role not in roles:
        raise HTTPException(
            status_code=403,
            detail=f"Role '{user.role}' not allowed. Required: {', '.join(roles)}",
        )


def require_admin(user: User) -> None:
    """Shortcut: only owner or admin."""
    require_role(user, "owner", "admin")
