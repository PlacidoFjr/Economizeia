from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime, timedelta
from uuid import UUID
import uuid

from app.db.database import get_db
from app.db.models import User, SavingsGoal, SavingsGoalStatus
from app.api.dependencies import get_current_user
from app.services.notification_service import notification_service
from app.services.audit_service import audit_service
from fastapi import Request

router = APIRouter()


class SavingsGoalCreate(BaseModel):
    name: str
    target_amount: float
    deadline: str  # YYYY-MM-DD
    description: Optional[str] = None
    notify_days_before: Optional[List[int]] = [30, 15, 7, 3, 1]


class SavingsGoalUpdate(BaseModel):
    name: Optional[str] = None
    target_amount: Optional[float] = None
    current_amount: Optional[float] = None
    deadline: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    notify_days_before: Optional[List[int]] = None


class SavingsGoalResponse(BaseModel):
    id: str
    name: str
    target_amount: float
    current_amount: float
    deadline: str
    description: Optional[str]
    status: str
    progress_percentage: float
    days_remaining: int
    notify_days_before: List[int]
    created_at: str
    updated_at: Optional[str]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_savings_goal(
    goal_data: SavingsGoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Criar uma nova meta de economia."""
    deadline = datetime.fromisoformat(goal_data.deadline).date()
    
    if deadline < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A data limite não pode ser no passado"
        )
    
    goal = SavingsGoal(
        id=uuid.uuid4(),
        user_id=current_user.id,
        name=goal_data.name,
        target_amount=goal_data.target_amount,
        current_amount=0.0,
        deadline=deadline,
        description=goal_data.description,
        status=SavingsGoalStatus.ACTIVE,
        notify_days_before=goal_data.notify_days_before
    )
    
    db.add(goal)
    db.commit()
    db.refresh(goal)
    
    # Audit log
    audit_service.log_action(
        db=db,
        entity="savings_goal",
        action="create",
        user_id=current_user.id,
        details={"goal_id": str(goal.id), "name": goal.name},
        request=request
    )
    
    return {
        "id": str(goal.id),
        "name": goal.name,
        "target_amount": goal.target_amount,
        "current_amount": goal.current_amount,
        "deadline": goal.deadline.isoformat(),
        "status": goal.status.value
    }


@router.get("")
async def list_savings_goals(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Listar todas as metas de economia do usuário."""
    query = db.query(SavingsGoal).filter(SavingsGoal.user_id == current_user.id)
    
    if status_filter:
        query = query.filter(SavingsGoal.status == SavingsGoalStatus(status_filter))
    
    goals = query.order_by(SavingsGoal.deadline).all()
    
    today = date.today()
    result = []
    
    for goal in goals:
        days_remaining = (goal.deadline - today).days
        progress = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
        
        # Atualizar status se necessário
        if goal.status == SavingsGoalStatus.ACTIVE:
            if goal.current_amount >= goal.target_amount:
                goal.status = SavingsGoalStatus.COMPLETED
            elif days_remaining < 0:
                goal.status = SavingsGoalStatus.EXPIRED
        
        result.append({
            "id": str(goal.id),
            "name": goal.name,
            "target_amount": goal.target_amount,
            "current_amount": goal.current_amount,
            "deadline": goal.deadline.isoformat(),
            "description": goal.description,
            "status": goal.status.value,
            "progress_percentage": round(progress, 2),
            "days_remaining": days_remaining,
            "notify_days_before": goal.notify_days_before or [30, 15, 7, 3, 1],
            "created_at": goal.created_at.isoformat() if goal.created_at else None,
            "updated_at": goal.updated_at.isoformat() if goal.updated_at else None
        })
    
    db.commit()
    return result


@router.get("/{goal_id}")
async def get_savings_goal(
    goal_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obter detalhes de uma meta específica."""
    goal = db.query(SavingsGoal).filter(
        and_(SavingsGoal.id == goal_id, SavingsGoal.user_id == current_user.id)
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meta não encontrada"
        )
    
    today = date.today()
    days_remaining = (goal.deadline - today).days
    progress = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
    
    return {
        "id": str(goal.id),
        "name": goal.name,
        "target_amount": goal.target_amount,
        "current_amount": goal.current_amount,
        "deadline": goal.deadline.isoformat(),
        "description": goal.description,
        "status": goal.status.value,
        "progress_percentage": round(progress, 2),
        "days_remaining": days_remaining,
        "notify_days_before": goal.notify_days_before or [30, 15, 7, 3, 1],
        "created_at": goal.created_at.isoformat() if goal.created_at else None,
        "updated_at": goal.updated_at.isoformat() if goal.updated_at else None
    }


@router.put("/{goal_id}")
async def update_savings_goal(
    goal_id: UUID,
    goal_data: SavingsGoalUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Atualizar uma meta de economia."""
    goal = db.query(SavingsGoal).filter(
        and_(SavingsGoal.id == goal_id, SavingsGoal.user_id == current_user.id)
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meta não encontrada"
        )
    
    if goal_data.name:
        goal.name = goal_data.name
    if goal_data.target_amount is not None:
        goal.target_amount = goal_data.target_amount
    if goal_data.current_amount is not None:
        goal.current_amount = goal_data.current_amount
        # Verificar se completou
        if goal.current_amount >= goal.target_amount and goal.status == SavingsGoalStatus.ACTIVE:
            goal.status = SavingsGoalStatus.COMPLETED
    if goal_data.deadline:
        deadline = datetime.fromisoformat(goal_data.deadline).date()
        if deadline < date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A data limite não pode ser no passado"
            )
        goal.deadline = deadline
    if goal_data.description is not None:
        goal.description = goal_data.description
    if goal_data.status:
        goal.status = SavingsGoalStatus(goal_data.status)
    if goal_data.notify_days_before:
        goal.notify_days_before = goal_data.notify_days_before
    
    db.commit()
    db.refresh(goal)
    
    # Audit log
    audit_service.log_action(
        db=db,
        entity="savings_goal",
        action="update",
        user_id=current_user.id,
        details={"goal_id": str(goal.id)},
        request=request
    )
    
    today = date.today()
    days_remaining = (goal.deadline - today).days
    progress = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
    
    return {
        "id": str(goal.id),
        "name": goal.name,
        "target_amount": goal.target_amount,
        "current_amount": goal.current_amount,
        "deadline": goal.deadline.isoformat(),
        "description": goal.description,
        "status": goal.status.value,
        "progress_percentage": round(progress, 2),
        "days_remaining": days_remaining
    }


@router.post("/{goal_id}/add-amount")
async def add_amount_to_goal(
    goal_id: UUID,
    amount: float,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Adicionar valor à meta de economia."""
    goal = db.query(SavingsGoal).filter(
        and_(SavingsGoal.id == goal_id, SavingsGoal.user_id == current_user.id)
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meta não encontrada"
        )
    
    if goal.status != SavingsGoalStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Só é possível adicionar valor a metas ativas"
        )
    
    goal.current_amount += amount
    
    # Verificar se completou
    if goal.current_amount >= goal.target_amount:
        goal.status = SavingsGoalStatus.COMPLETED
    
    db.commit()
    db.refresh(goal)
    
    # Audit log
    audit_service.log_action(
        db=db,
        entity="savings_goal",
        action="add_amount",
        user_id=current_user.id,
        details={"goal_id": str(goal.id), "amount": amount},
        request=request
    )
    
    today = date.today()
    days_remaining = (goal.deadline - today).days
    progress = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
    
    return {
        "id": str(goal.id),
        "current_amount": goal.current_amount,
        "progress_percentage": round(progress, 2),
        "days_remaining": days_remaining,
        "status": goal.status.value
    }


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_savings_goal(
    goal_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Deletar uma meta de economia."""
    goal = db.query(SavingsGoal).filter(
        and_(SavingsGoal.id == goal_id, SavingsGoal.user_id == current_user.id)
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meta não encontrada"
        )
    
    # Audit log
    audit_service.log_action(
        db=db,
        entity="savings_goal",
        action="delete",
        user_id=current_user.id,
        details={"goal_id": str(goal.id), "name": goal.name},
        request=request
    )
    
    db.delete(goal)
    db.commit()

