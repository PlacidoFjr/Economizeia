"""Authenticated financial assistant. All writes require a server-side draft."""
import logging
import re
from typing import Optional, List, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.services.financial_chat_service import clear_history, handle_financial_chat, monthly_financial_overview, read_history, user_today

from app.services.financial_plan_editor import PlanEdit, delete_item, list_items, update_item

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatMessage(BaseModel):
    message: str = Field(min_length=1, max_length=16000)
    conversation_history: Optional[List[Dict]] = None  # legacy client compatibility; never trusted for writes
    request_id: Optional[UUID] = None
    draft_id: Optional[str] = Field(default=None, max_length=64)


class ChatResponse(BaseModel):
    response: str
    action: Optional[str] = None
    bill_id: Optional[str] = None
    draft_id: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
def chat_with_assistant(chat_data: ChatMessage, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return handle_financial_chat(chat_data.message, current_user, db, chat_data.request_id, chat_data.draft_id)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.error("Financial chat request failed (%s)", type(exc).__name__)
        raise HTTPException(status_code=500, detail="Não foi possível processar a mensagem. Nenhuma alteração parcial foi salva.")


@router.get("/overview")
def financial_overview(month: Optional[str] = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    today = user_today(current_user)
    month = month or today.strftime("%Y-%m")
    if not re.fullmatch(r"20\d{2}-(0[1-9]|1[0-2])", month):
        raise HTTPException(status_code=422, detail="Informe o mês no formato AAAA-MM.")
    return monthly_financial_overview(db, current_user.id, month, today)


@router.get("/history")
def history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return read_history(db, current_user.id)


@router.delete("/history", status_code=204)
def delete_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    clear_history(db, current_user.id)


@router.get("/plan-items")
def financial_plan_items(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_items(db, current_user.id)


@router.put("/plan-items/{item_id}")
def update_plan_item(item_id: UUID, edit: PlanEdit, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return update_item(db, current_user.id, item_id, edit, user_today(current_user))


@router.delete("/plan-items/{item_id}", status_code=204)
def delete_plan_item(item_id: UUID, version: str = Query(pattern=r"^[a-f0-9]{64}$"),
                     current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    delete_item(db, current_user.id, item_id, version)
