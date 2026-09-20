import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.budget import Budget
from app.models.user import User
from app.schemas.budget import BudgetCreate, BudgetProgress, BudgetUpdate
from app.services import budget_service

router = APIRouter()


def _get_owned_budget(db: Session, budget_id: uuid.UUID, user_id: uuid.UUID) -> Budget:
    budget = db.execute(
        select(Budget).where(Budget.id == budget_id, Budget.user_id == user_id)
    ).scalar_one_or_none()
    if budget is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
    return budget


@router.get("", response_model=list[BudgetProgress])
def list_budgets(
    month: int | None = None,
    year: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[BudgetProgress]:
    stmt = select(Budget).where(Budget.user_id == current_user.id)
    if month is not None:
        stmt = stmt.where(Budget.month == month)
    if year is not None:
        stmt = stmt.where(Budget.year == year)
    budgets = db.execute(stmt.order_by(Budget.year.desc(), Budget.month.desc())).scalars().all()
    return [budget_service.to_progress(db, current_user.id, b) for b in budgets]


@router.post("", response_model=BudgetProgress, status_code=status.HTTP_201_CREATED)
def create_budget(
    payload: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BudgetProgress:
    budget = Budget(user_id=current_user.id, **payload.model_dump())
    db.add(budget)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A budget for this category and month already exists",
        ) from exc
    db.refresh(budget)
    return budget_service.to_progress(db, current_user.id, budget)


@router.patch("/{budget_id}", response_model=BudgetProgress)
def update_budget(
    budget_id: uuid.UUID,
    payload: BudgetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BudgetProgress:
    budget = _get_owned_budget(db, budget_id, current_user.id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(budget, field, value)
    db.commit()
    db.refresh(budget)
    return budget_service.to_progress(db, current_user.id, budget)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    budget = _get_owned_budget(db, budget_id, current_user.id)
    db.delete(budget)
    db.commit()
