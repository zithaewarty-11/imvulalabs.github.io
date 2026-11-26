from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.audit import record_audit
from app.core.database import get_db
from app.core.permissions import require_admin
from app.deps import get_current_user
from app.models.assessment import Assessment, AssessmentFinding
from app.models.user import User
from app.schemas.assessment import (
    AssessmentCreate, AssessmentOut, AssessmentUpdate,
    FindingCreate, FindingOut,
)

router = APIRouter(prefix="/assessments", tags=["assessments"])


def _get_assessment_or_404(db: Session, assessment_id: int, org_id: int) -> Assessment:
    a = db.get(Assessment, assessment_id)
    if a is None or a.org_id != org_id:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return a


@router.post("", response_model=AssessmentOut, status_code=201)
def create_assessment(
    body: AssessmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    assessment = Assessment(org_id=user.org_id, created_by=user.id, **body.model_dump())
    db.add(assessment)
    db.flush()
    record_audit(
        db, org_id=user.org_id, actor_id=user.id,
        action="assessment.created", target_type="assessment",
        target_id=assessment.id, details=body.name,
    )
    db.commit()
    db.refresh(assessment)
    return assessment


@router.get("", response_model=list[AssessmentOut])
def list_assessments(
    status: str | None = None,
    assessment_type: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(Assessment).filter(Assessment.org_id == user.org_id)
    if status:
        q = q.filter(Assessment.status == status)
    if assessment_type:
        q = q.filter(Assessment.assessment_type == assessment_type)
    return q.order_by(Assessment.id.desc()).all()


@router.get("/{assessment_id}", response_model=AssessmentOut)
def get_assessment(
    assessment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return _get_assessment_or_404(db, assessment_id, user.org_id)


@router.patch("/{assessment_id}", response_model=AssessmentOut)
def update_assessment(
    assessment_id: int,
    body: AssessmentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_admin(user)
    assessment = _get_assessment_or_404(db, assessment_id, user.org_id)
    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(assessment, field, value)
    record_audit(
        db, org_id=user.org_id, actor_id=user.id,
        action="assessment.updated", target_type="assessment",
        target_id=assessment.id, details=",".join(updates.keys()),
    )
    db.commit()
    db.refresh(assessment)
    return assessment


@router.post("/{assessment_id}/findings", response_model=FindingOut, status_code=201)
def create_finding(
    assessment_id: int,
    body: FindingCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _get_assessment_or_404(db, assessment_id, user.org_id)
    finding = AssessmentFinding(
        org_id=user.org_id, assessment_id=assessment_id,
        created_by=user.id, **body.model_dump(),
    )
    db.add(finding)
    db.commit()
    db.refresh(finding)
    return finding


@router.get("/{assessment_id}/findings", response_model=list[FindingOut])
def list_findings(
    assessment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _get_assessment_or_404(db, assessment_id, user.org_id)
    return (
        db.query(AssessmentFinding)
        .filter(
            AssessmentFinding.assessment_id == assessment_id,
            AssessmentFinding.org_id == user.org_id,
        )
        .order_by(AssessmentFinding.id.desc())
        .all()
    )
