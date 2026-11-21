from datetime import datetime

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    assignee_id: int | None = None
    due_date: datetime | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: str | None = Field(
        default=None, pattern="^(todo|in_progress|blocked|done)$"
    )
    priority: str | None = Field(
        default=None, pattern="^(low|medium|high|critical)$"
    )
    assignee_id: int | None = None
    due_date: datetime | None = None


class TaskOut(BaseModel):
    id: int
    org_id: int
    title: str
    description: str
    status: str
    priority: str
    assignee_id: int | None
    due_date: datetime | None
    created_by: int
    model_config = {"from_attributes": True}
