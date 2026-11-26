from datetime import datetime
from pydantic import BaseModel, Field


class AssessmentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    description: str = ""
    target: str = Field(min_length=3, max_length=500)
    assessment_type: str = Field(
        pattern="^(web_app|api|vulnerability|code_review)$"
    )
    scope: str = ""
    authorisation_proof: str = Field(min_length=10)


class AssessmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    scope: str | None = None
    status: str | None = Field(
        default=None, pattern="^(pending|in_progress|completed|archived)$"
    )


class AssessmentOut(BaseModel):
    id: int
    org_id: int
    name: str
    description: str
    target: str
    assessment_type: str
    scope: str
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}


class FindingCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str = ""
    severity: str = Field(pattern="^(critical|high|medium|low)$")
    remediation: str = ""


class FindingOut(BaseModel):
    id: int
    assessment_id: int
    title: str
    description: str
    severity: str
    remediation: str
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}
