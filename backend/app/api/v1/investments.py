from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from uuid import UUID
import uuid

from app.db.database import get_db
from app.db.models import User, Investment, InvestmentType
from app.api.dependencies import get_current_user
from app.services.audit_service import audit_service
from fastapi import Request

router = APIRouter()


class InvestmentCreate(BaseModel):
    name: str
    type: str
    amount_invested: float
    purchase_date: str  # YYYY-MM-DD
    institution: Optional[str] = None
    ticker: Optional[str] = None
    notes: Optional[str] = None
    current_value: Optional[float] = None


class InvestmentUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    amount_invested: Optional[float] = None
    current_value: Optional[float] = None
    purchase_date: Optional[str] = None
    sell_date: Optional[str] = None
    institution: Optional[str] = None
    ticker: Optional[str] = None
    notes: Optional[str] = None


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_investment(
    investment_data: InvestmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Criar um novo investimento."""
    purchase_date = datetime.fromisoformat(investment_data.purchase_date).date()
    
    if purchase_date > date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A data de compra não pode ser no futuro"
        )
    
    try:
        investment_type = InvestmentType(investment_data.type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de investimento inválido. Tipos válidos: {[e.value for e in InvestmentType]}"
        )
    
    investment = Investment(
        id=uuid.uuid4(),
        user_id=current_user.id,
        name=investment_data.name,
        type=investment_type,
        amount_invested=investment_data.amount_invested,
        current_value=investment_data.current_value or investment_data.amount_invested,
        purchase_date=purchase_date,
        institution=investment_data.institution,
        ticker=investment_data.ticker,
        notes=investment_data.notes
    )
    
    db.add(investment)
    db.commit()
    db.refresh(investment)
    
    # Audit log
    audit_service.log_action(
        db=db,
        entity="investment",
        action="create",
        user_id=current_user.id,
        details={"investment_id": str(investment.id), "name": investment.name},
        request=request
    )
    
    return {
        "id": str(investment.id),
        "name": investment.name,
        "type": investment.type.value,
        "amount_invested": investment.amount_invested,
        "current_value": investment.current_value,
        "purchase_date": investment.purchase_date.isoformat(),
        "institution": investment.institution,
        "ticker": investment.ticker
    }


@router.get("")
async def list_investments(
    type_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Listar todos os investimentos do usuário."""
    query = db.query(Investment).filter(Investment.user_id == current_user.id)
    
    if type_filter:
        try:
            investment_type = InvestmentType(type_filter)
            query = query.filter(Investment.type == investment_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de investimento inválido"
            )
    
    investments = query.order_by(Investment.purchase_date.desc()).all()
    
    result = []
    for inv in investments:
        profit_loss = (inv.current_value or inv.amount_invested) - inv.amount_invested
        profit_loss_percentage = (profit_loss / inv.amount_invested * 100) if inv.amount_invested > 0 else 0
        
        result.append({
            "id": str(inv.id),
            "name": inv.name,
            "type": inv.type.value,
            "amount_invested": inv.amount_invested,
            "current_value": inv.current_value,
            "purchase_date": inv.purchase_date.isoformat(),
            "sell_date": inv.sell_date.isoformat() if inv.sell_date else None,
            "institution": inv.institution,
            "ticker": inv.ticker,
            "notes": inv.notes,
            "profit_loss": round(profit_loss, 2),
            "profit_loss_percentage": round(profit_loss_percentage, 2),
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
            "updated_at": inv.updated_at.isoformat() if inv.updated_at else None
        })
    
    return result


@router.get("/{investment_id}")
async def get_investment(
    investment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obter detalhes de um investimento específico."""
    investment = db.query(Investment).filter(
        and_(Investment.id == investment_id, Investment.user_id == current_user.id)
    ).first()
    
    if not investment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investimento não encontrado"
        )
    
    profit_loss = (investment.current_value or investment.amount_invested) - investment.amount_invested
    profit_loss_percentage = (profit_loss / investment.amount_invested * 100) if investment.amount_invested > 0 else 0
    
    return {
        "id": str(investment.id),
        "name": investment.name,
        "type": investment.type.value,
        "amount_invested": investment.amount_invested,
        "current_value": investment.current_value,
        "purchase_date": investment.purchase_date.isoformat(),
        "sell_date": investment.sell_date.isoformat() if investment.sell_date else None,
        "institution": investment.institution,
        "ticker": investment.ticker,
        "notes": investment.notes,
        "profit_loss": round(profit_loss, 2),
        "profit_loss_percentage": round(profit_loss_percentage, 2),
        "created_at": investment.created_at.isoformat() if investment.created_at else None,
        "updated_at": investment.updated_at.isoformat() if investment.updated_at else None
    }


@router.put("/{investment_id}")
async def update_investment(
    investment_id: UUID,
    investment_data: InvestmentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Atualizar um investimento."""
    investment = db.query(Investment).filter(
        and_(Investment.id == investment_id, Investment.user_id == current_user.id)
    ).first()
    
    if not investment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investimento não encontrado"
        )
    
    if investment_data.name:
        investment.name = investment_data.name
    if investment_data.type:
        try:
            investment.type = InvestmentType(investment_data.type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de investimento inválido"
            )
    if investment_data.amount_invested is not None:
        investment.amount_invested = investment_data.amount_invested
    if investment_data.current_value is not None:
        investment.current_value = investment_data.current_value
    if investment_data.purchase_date:
        purchase_date = datetime.fromisoformat(investment_data.purchase_date).date()
        if purchase_date > date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A data de compra não pode ser no futuro"
            )
        investment.purchase_date = purchase_date
    if investment_data.sell_date is not None:
        if investment_data.sell_date:
            sell_date = datetime.fromisoformat(investment_data.sell_date).date()
            if sell_date < investment.purchase_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A data de venda não pode ser anterior à data de compra"
                )
            investment.sell_date = sell_date
        else:
            investment.sell_date = None
    if investment_data.institution is not None:
        investment.institution = investment_data.institution
    if investment_data.ticker is not None:
        investment.ticker = investment_data.ticker
    if investment_data.notes is not None:
        investment.notes = investment_data.notes
    
    db.commit()
    db.refresh(investment)
    
    # Audit log
    audit_service.log_action(
        db=db,
        entity="investment",
        action="update",
        user_id=current_user.id,
        details={"investment_id": str(investment.id)},
        request=request
    )
    
    profit_loss = (investment.current_value or investment.amount_invested) - investment.amount_invested
    profit_loss_percentage = (profit_loss / investment.amount_invested * 100) if investment.amount_invested > 0 else 0
    
    return {
        "id": str(investment.id),
        "name": investment.name,
        "type": investment.type.value,
        "amount_invested": investment.amount_invested,
        "current_value": investment.current_value,
        "profit_loss": round(profit_loss, 2),
        "profit_loss_percentage": round(profit_loss_percentage, 2)
    }


@router.delete("/{investment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_investment(
    investment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Deletar um investimento."""
    investment = db.query(Investment).filter(
        and_(Investment.id == investment_id, Investment.user_id == current_user.id)
    ).first()
    
    if not investment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investimento não encontrado"
        )
    
    # Audit log
    audit_service.log_action(
        db=db,
        entity="investment",
        action="delete",
        user_id=current_user.id,
        details={"investment_id": str(investment.id), "name": investment.name},
        request=request
    )
    
    db.delete(investment)
    db.commit()


