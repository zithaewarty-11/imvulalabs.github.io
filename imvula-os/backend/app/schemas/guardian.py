from datetime import datetime

from pydantic import BaseModel, Field


# ── Agents ──
class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = ""
    kind: str = Field(pattern="^(analyst|planner|executor)$")


class AgentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    active: bool | None = None


class AgentOut(BaseModel):
    id: int
    org_id: int
    name: str
    description: str
    kind: str
    active: bool
    created_by: int
    model_config = {"from_attributes": True}


# ── Agent runs ──
class AgentRunCreate(BaseModel):
    agent_id: int
    request: str = Field(min_length=1)


class AgentRunDecision(BaseModel):
    """Used when an admin approves or rejects a pending run."""
    result: str = ""


class AgentRunOut(BaseModel):
    id: int
    org_id: int
    agent_id: int
    status: str
    request: str
    result: str
    created_by: int
    created_at: datetime
    decided_by: int | None
    decided_at: datetime | None
    model_config = {"from_attributes": True}
