from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record_audit
from app.core.database import get_db
from app.core.permissions import require_admin
from app.deps import get_current_user
from app.models.automation import Task
from app.models.user import User
from app.schemas.automation import TaskCreate, TaskOut, TaskUpdate

router = APIRouter(prefix="/automation", tags=["automation"])


def _get_task_or_404(db: Session, task_id: int, org_id: int) -> Task:
    task = db.get(Task, task_id)
    if task is None or task.org_id != org_id:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


def _validate_assignee(db: Session, assignee_id: int | None, org_id: int) -> None:
    if assignee_id is None:
        return
    assignee = db.get(User, assignee_id)
    if assignee is None or assignee.org_id != org_id:
        raise HTTPException(
            status_code=400, detail="Assignee must belong to your organisation"
        )


@router.post("/tasks", response_model=TaskOut, status_code=201)
def create_task(
    body: TaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _validate_assignee(db, body.assignee_id, user.org_id)
    task = Task(org_id=user.org_id, created_by=user.id, **body.model_dump())
    db.add(task)
    db.flush()
    record_audit(
        db,
        org_id=user.org_id,
        actor_id=user.id,
        action="task.created",
        target_type="task",
        target_id=task.id,
        details=body.title,
    )
    db.commit()
    db.refresh(task)
    return task


@router.get("/tasks", response_model=list[TaskOut])
def list_tasks(
    status_filter: str | None = None,
    priority: str | None = None,
    assignee_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(Task).filter(Task.org_id == user.org_id)
    if status_filter:
        q = q.filter(Task.status == status_filter)
    if priority:
        q = q.filter(Task.priority == priority)
    if assignee_id is not None:
        q = q.filter(Task.assignee_id == assignee_id)
    return q.order_by(Task.id.desc()).all()


@router.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return _get_task_or_404(db, task_id, user.org_id)


@router.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    body: TaskUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = _get_task_or_404(db, task_id, user.org_id)
    updates = body.model_dump(exclude_unset=True)
    if "assignee_id" in updates:
        _validate_assignee(db, updates["assignee_id"], user.org_id)
    for field, value in updates.items():
        setattr(task, field, value)
    record_audit(
        db,
        org_id=user.org_id,
        actor_id=user.id,
        action="task.updated",
        target_type="task",
        target_id=task.id,
        details=",".join(updates.keys()) if updates else "",
    )
    db.commit()
    db.refresh(task)
    return task


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_admin(user)
    task = _get_task_or_404(db, task_id, user.org_id)
    db.delete(task)
    db.commit()
    return None
