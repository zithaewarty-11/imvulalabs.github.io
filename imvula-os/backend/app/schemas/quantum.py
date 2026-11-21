from datetime import datetime

from pydantic import BaseModel, Field


class AssetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    asset_type: str = Field(pattern="^(website|email|server|database|saas_app|other)$")
    criticality: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    description: str = ""


class AssetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    asset_type: str | None = Field(
        default=None, pattern="^(website|email|server|database|saas_app|other)$"
    )
    criticality: str | None = Field(
        default=None, pattern="^(low|medium|high|critical)$"
    )
    description: str | None = None


class AssetOut(BaseModel):
    id: int
    org_id: int
    name: str
    asset_type: str
    criticality: str
    description: str
    model_config = {"from_attributes": True}


class RiskCreate(BaseModel):
    asset_id: int
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    severity: str = Field(default="medium", pattern="^(low|medium|high|critical)$")


class RiskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    severity: str | None = Field(
        default=None, pattern="^(low|medium|high|critical)$"
    )
    status: str | None = Field(
        default=None, pattern="^(open|in_progress|resolved|accepted)$"
    )


class RiskOut(BaseModel):
    id: int
    org_id: int
    asset_id: int
    title: str
    description: str
    severity: str
    status: str
    model_config = {"from_attributes": True}


class RemediationCreate(BaseModel):
    risk_id: int
    description: str = Field(min_length=1)
    due_date: datetime | None = None


class RemediationUpdate(BaseModel):
    description: str | None = Field(default=None, min_length=1)
    status: str | None = Field(
        default=None, pattern="^(pending|in_progress|done)$"
    )
    due_date: datetime | None = None


class RemediationOut(BaseModel):
    id: int
    org_id: int
    risk_id: int
    description: str
    status: str
    due_date: datetime | None = None
    model_config = {"from_attributes": True}
