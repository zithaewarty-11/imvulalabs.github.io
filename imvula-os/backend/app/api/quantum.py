from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record_audit
from app.core.database import get_db
from app.core.permissions import require_admin
from app.deps import get_current_user
from app.models.quantum import Asset, Remediation, Risk
from app.models.user import User
from app.schemas.quantum import (
    AssetCreate,
    AssetOut,
    AssetUpdate,
    RemediationCreate,
    RemediationOut,
    RemediationUpdate,
    RiskCreate,
    RiskOut,
    RiskUpdate,
)

router = APIRouter(prefix="/quantum", tags=["quantum-shield"])


def _get_asset_or_404(db: Session, asset_id: int, org_id: int) -> Asset:
    asset = db.get(Asset, asset_id)
    if asset is None or asset.org_id != org_id:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


def _get_risk_or_404(db: Session, risk_id: int, org_id: int) -> Risk:
    risk = db.get(Risk, risk_id)
    if risk is None or risk.org_id != org_id:
        raise HTTPException(status_code=404, detail="Risk not found")
    return risk


def _get_remediation_or_404(
    db: Session, remediation_id: int, org_id: int
) -> Remediation:
    rem = db.get(Remediation, remediation_id)
    if rem is None or rem.org_id != org_id:
        raise HTTPException(status_code=404, detail="Remediation not found")
    return rem


@router.post("/assets", response_model=AssetOut, status_code=201)
def create_asset(
    body: AssetCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    asset = Asset(org_id=user.org_id, created_by=user.id, **body.model_dump())
    db.add(asset)
    db.flush()
    record_audit(
        db,
        org_id=user.org_id,
        actor_id=user.id,
        action="asset.created",
        target_type="asset",
        target_id=asset.id,
        details=body.name,
    )
    db.commit()
    db.refresh(asset)
    return asset


@router.get("/assets", response_model=list[AssetOut])
def list_assets(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return (
        db.query(Asset)
        .filter(Asset.org_id == user.org_id)
        .order_by(Asset.id.desc())
        .all()
    )


@router.get("/assets/{asset_id}", response_model=AssetOut)
def get_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return _get_asset_or_404(db, asset_id, user.org_id)


@router.patch("/assets/{asset_id}", response_model=AssetOut)
def update_asset(
    asset_id: int,
    body: AssetUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    asset = _get_asset_or_404(db, asset_id, user.org_id)
    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(asset, field, value)
    record_audit(
        db,
        org_id=user.org_id,
        actor_id=user.id,
        action="asset.updated",
        target_type="asset",
        target_id=asset.id,
        details=",".join(updates.keys()) if updates else "",
    )
    db.commit()
    db.refresh(asset)
    return asset


@router.delete("/assets/{asset_id}", status_code=204)
def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_admin(user)
    asset = _get_asset_or_404(db, asset_id, user.org_id)
    if asset.risks:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete asset with existing risks. Delete the risks first.",
        )
    asset_name = asset.name
    asset_id_for_log = asset.id
    db.delete(asset)
    db.flush()
    record_audit(
        db,
        org_id=user.org_id,
        actor_id=user.id,
        action="asset.deleted",
        target_type="asset",
        target_id=asset_id_for_log,
        details=asset_name,
    )
    db.commit()
    return None


@router.post("/risks", response_model=RiskOut, status_code=201)
def create_risk(
    body: RiskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _get_asset_or_404(db, body.asset_id, user.org_id)

    risk = Risk(org_id=user.org_id, created_by=user.id, **body.model_dump())
    db.add(risk)
    db.flush()
    record_audit(
        db,
        org_id=user.org_id,
        actor_id=user.id,
        action="risk.created",
        target_type="risk",
        target_id=risk.id,
        details=body.title,
    )
    db.commit()
    db.refresh(risk)
    return risk


@router.get("/risks", response_model=list[RiskOut])
def list_risks(
    severity: str | None = None,
    status_filter: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(Risk).filter(Risk.org_id == user.org_id)
    if severity:
        q = q.filter(Risk.severity == severity)
    if status_filter:
        q = q.filter(Risk.status == status_filter)
    return q.order_by(Risk.id.desc()).all()


@router.get("/risks/{risk_id}", response_model=RiskOut)
def get_risk(
    risk_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return _get_risk_or_404(db, risk_id, user.org_id)
@router.patch("/risks/{risk_id}", response_model=RiskOut)
def update_risk(
    risk_id: int,
    body: RiskUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    risk = _get_risk_or_404(db, risk_id, user.org_id)
    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(risk, field, value)
    record_audit(
        db,
        org_id=user.org_id,
        actor_id=user.id,
        action="risk.updated",
        target_type="risk",
        target_id=risk.id,
        details=",".join(updates.keys()) if updates else "",
    )
    db.commit()
    db.refresh(risk)
    return risk


@router.post("/remediations", response_model=RemediationOut, status_code=201)
def create_remediation(
    body: RemediationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _get_risk_or_404(db, body.risk_id, user.org_id)
    rem = Remediation(org_id=user.org_id, created_by=user.id, **body.model_dump())
    db.add(rem)
    db.commit()
    db.refresh(rem)
    return rem


@router.get(
    "/risks/{risk_id}/remediations", response_model=list[RemediationOut]
)
def list_remediations_for_risk(
    risk_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _get_risk_or_404(db, risk_id, user.org_id)
    return (
        db.query(Remediation)
        .filter(
            Remediation.risk_id == risk_id,
            Remediation.org_id == user.org_id,
        )
        .all()
    )


@router.patch("/remediations/{remediation_id}", response_model=RemediationOut)
def update_remediation(
    remediation_id: int,
    body: RemediationUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rem = _get_remediation_or_404(db, remediation_id, user.org_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(rem, field, value)
    db.commit()
    db.refresh(rem)
    return rem


@router.get("/assets/{asset_id}/history")
def asset_history(
    asset_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Fetch the audit trail for a specific asset."""
    _get_asset_or_404(db, asset_id, user.org_id)
    from app.models.audit import AuditEvent
    
    events = (
        db.query(AuditEvent)
        .filter(
            AuditEvent.org_id == user.org_id,
            AuditEvent.target_type == "asset",
            AuditEvent.target_id == asset_id
        )
        .order_by(AuditEvent.created_at.desc())
        .all()
    )
    return [
        {
            "id": e.id,
            "action": e.action,
            "details": e.details,
            "created_at": e.created_at,
            "actor_id": e.actor_id
        }
        for e in events
    ]


@router.get("/risks/{risk_id}/history")
def risk_history(
    risk_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Fetch the audit trail for a specific risk/vulnerability."""
    _get_risk_or_404(db, risk_id, user.org_id)
    from app.models.audit import AuditEvent
    events = (
        db.query(AuditEvent)
        .filter(
            AuditEvent.org_id == user.org_id,
            AuditEvent.target_type == "risk",
            AuditEvent.target_id == risk_id,
        )
        .order_by(AuditEvent.created_at.desc())
        .all()
    )
    return [
        {
            "id": e.id,
            "action": e.action,
            "details": e.details,
            "created_at": e.created_at,
            "actor_id": e.actor_id,
        }
        for e in events
    ]
