from sqlalchemy.orm import Session
from app.db.models import AuditLog
import uuid
from typing import Optional, Dict, Any
from fastapi import Request


class AuditService:
    """Service for creating immutable audit logs."""
    
    @staticmethod
    def log_action(
        db: Session,
        entity: str,
        action: str,
        user_id: Optional[uuid.UUID] = None,
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ):
        """Create an audit log entry."""
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
        
        audit_log = AuditLog(
            id=uuid.uuid4(),
            entity=entity,
            action=action,
            user_id=user_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(audit_log)
        db.commit()
        
        return audit_log


audit_service = AuditService()

