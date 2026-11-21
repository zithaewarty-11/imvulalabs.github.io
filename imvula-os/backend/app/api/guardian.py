from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record_audit
from app.core.database import get_db
from app.core.permissions import require_admin
from app.deps import get_current_user
from app.models.guardian import Agent, AgentRun
from app.models.user import User
from app.schemas.guardian import (
    AgentCreate,
    AgentOut,
    AgentRunCreate,
    AgentRunDecision,
    AgentRunOut,
    AgentUpdate,
)

router = APIRouter(prefix="/guardian", tags=["guardian"])


def _get_agent_or_404(db: Session, agent_id: int, org_id: int) -> Agent:
    agent = db.get(Agent, agent_id)
    if agent is None or agent.org_id != org_id:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


def _get_run_or_404(db: Session, run_id: int, org_id: int) -> AgentRun:
    run = db.get(AgentRun, run_id)
    if run is None or run.org_id != org_id:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.post("/agents", response_model=AgentOut, status_code=201)
def create_agent(
    body: AgentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_admin(user)
    agent = Agent(org_id=user.org_id, created_by=user.id, **body.model_dump())
    db.add(agent)
    db.flush()
    record_audit(
        db,
        org_id=user.org_id,
        actor_id=user.id,
        action="agent.created",
        target_type="agent",
        target_id=agent.id,
        details=body.name,
    )
    db.commit()
    db.refresh(agent)
    return agent


@router.get("/agents", response_model=list[AgentOut])
def list_agents(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return (
        db.query(Agent)
        .filter(Agent.org_id == user.org_id)
        .order_by(Agent.id.desc())
        .all()
    )


@router.get("/agents/{agent_id}", response_model=AgentOut)
def get_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return _get_agent_or_404(db, agent_id, user.org_id)


@router.patch("/agents/{agent_id}", response_model=AgentOut)
def update_agent(
    agent_id: int,
    body: AgentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_admin(user)
    agent = _get_agent_or_404(db, agent_id, user.org_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(agent, field, value)
    db.commit()
    db.refresh(agent)
    return agent


@router.post("/runs", response_model=AgentRunOut, status_code=201)
def create_run(
    body: AgentRunCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    agent = _get_agent_or_404(db, body.agent_id, user.org_id)
    if not agent.active:
        raise HTTPException(status_code=400, detail="Agent is not active")

    run = AgentRun(
        org_id=user.org_id,
        agent_id=agent.id,
        request=body.request,
        created_by=user.id,
        status="pending_approval",
    )
    db.add(run)
    db.flush()
    record_audit(
        db,
        org_id=user.org_id,
        actor_id=user.id,
        action="agent_run.created",
        target_type="agent_run",
        target_id=run.id,
        details=agent.name,
    )
    db.commit()
    db.refresh(run)
    return run

@router.get("/runs", response_model=list[AgentRunOut])
def list_runs(
    status_filter: str | None = None,
    agent_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(AgentRun).filter(AgentRun.org_id == user.org_id)
    if status_filter:
        q = q.filter(AgentRun.status == status_filter)
    if agent_id is not None:
        q = q.filter(AgentRun.agent_id == agent_id)
    return q.order_by(AgentRun.id.desc()).all()


@router.get("/runs/{run_id}", response_model=AgentRunOut)
def get_run(
    run_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return _get_run_or_404(db, run_id, user.org_id)


@router.post("/runs/{run_id}/approve", response_model=AgentRunOut)
def approve_run(
    run_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_admin(user)
    run = _get_run_or_404(db, run_id, user.org_id)
    if run.status != "pending_approval":
        raise HTTPException(
            status_code=409,
            detail=f"Cannot approve run in status '{run.status}'",
        )
    run.status = "approved"
    run.decided_by = user.id
    run.decided_at = datetime.now(timezone.utc).replace(tzinfo=None)
    record_audit(
        db,
        org_id=user.org_id,
        actor_id=user.id,
        action="agent_run.approved",
        target_type="agent_run",
        target_id=run.id,
        details="",
    )
    db.commit()
    db.refresh(run)
    return run


@router.post("/runs/{run_id}/reject", response_model=AgentRunOut)
def reject_run(
    run_id: int,
    body: AgentRunDecision | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_admin(user)
    run = _get_run_or_404(db, run_id, user.org_id)
    if run.status != "pending_approval":
        raise HTTPException(
            status_code=409,
            detail=f"Cannot reject run in status '{run.status}'",
        )
    run.status = "rejected"
    run.decided_by = user.id
    run.decided_at = datetime.now(timezone.utc).replace(tzinfo=None)
    if body and body.result:
        run.result = body.result
    record_audit(
        db,
        org_id=user.org_id,
        actor_id=user.id,
        action="agent_run.rejected",
        target_type="agent_run",
        target_id=run.id,
        details=body.result if body else "",
    )
    db.commit()
    db.refresh(run)
    return run


@router.post("/runs/{run_id}/complete", response_model=AgentRunOut)
def complete_run(
    run_id: int,
    body: AgentRunDecision | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    run = _get_run_or_404(db, run_id, user.org_id)
    if run.status != "approved":
        raise HTTPException(
            status_code=409,
            detail=f"Cannot complete run in status '{run.status}'",
        )
    run.status = "completed"
    if body and body.result:
        run.result = body.result
    db.commit()
    db.refresh(run)
    return run
