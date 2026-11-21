from datetime import datetime

from pydantic import BaseModel, Field


class AICompleteRequest(BaseModel):
    """What a user sends when asking the AI a question."""
    prompt: str = Field(min_length=1, max_length=4000)
    max_tokens: int = Field(default=512, ge=1, le=2048)
    # Optional: attach the answer to a Guardian run for approval tracking
    guardian_run_id: int | None = None


class AICompleteResponse(BaseModel):
    """What comes back after the AI answers."""
    response: str
    provider: str
    model: str
    prompt_chars: int
    response_chars: int


class AIUsageOut(BaseModel):
    """One usage record — for admin dashboards and billing review."""
    id: int
    org_id: int
    user_id: int
    provider: str
    model: str
    prompt_preview: str
    prompt_chars: int
    response_chars: int
    success: bool
    error_message: str
    created_at: datetime
    model_config = {"from_attributes": True}
