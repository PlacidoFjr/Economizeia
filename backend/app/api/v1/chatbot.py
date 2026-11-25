"""Authenticated financial assistant. All writes require a server-side draft."""
import logging
from typing import Optional, List, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.services.financial_chat_service import handle_financial_chat

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatMessage(BaseModel):
    message: str = Field(min_length=1, max_length=16000)
    conversation_history: Optional[List[Dict]] = None  # legacy client compatibility; never trusted for writes


class ChatResponse(BaseModel):
    response: str
    action: Optional[str] = None
    bill_id: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(chat_data: ChatMessage, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return handle_financial_chat(chat_data.message, current_user, db)
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        logger.exception("Financial chat request failed")
        raise HTTPException(status_code=500, detail="Não foi possível processar a mensagem. Nenhuma alteração parcial foi salva.")
