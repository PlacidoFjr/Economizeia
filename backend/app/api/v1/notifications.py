from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

from app.db.database import get_db
from app.db.models import User, Notification, NotificationChannel, NotificationType
from app.api.dependencies import get_current_user
from app.services.notification_service import notification_service

router = APIRouter()


class TestNotificationRequest(BaseModel):
    user_id: Optional[str] = None
    type: str
    channel: str


@router.post("/test")
async def test_notification(
    test_data: TestNotificationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test notification sending."""
    user = current_user
    if test_data.user_id:
        user = db.query(User).filter(User.id == test_data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
    
    channel = NotificationChannel(test_data.channel)
    notif_type = NotificationType(test_data.type)
    
    if channel == NotificationChannel.EMAIL:
        sent = await notification_service.send_email(
            user.email,
            "Test Notification",
            "This is a test notification from EconomizeIA"
        )
    elif channel == NotificationChannel.SMS:
        sent = await notification_service.send_sms(
            user.phone or "",
            "Test notification from EconomizeIA"
        )
    else:
        sent = await notification_service.send_push(
            user.id,
            "Test",
            "Test notification from EconomizeIA"
        )
    
    return {"sent": sent, "channel": channel.value}


@router.get("/logs")
async def get_notification_logs(
    user_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get notification logs."""
    query = db.query(Notification)
    
    # Only admin can see other users' notifications
    if user_id and user_id != str(current_user.id):
        # In production, check admin role
        pass
    
    if not user_id:
        user_id = str(current_user.id)
    
    query = query.filter(Notification.user_id == user_id)
    notifications = query.order_by(Notification.created_at.desc()).limit(100).all()
    
    return [
        {
            "id": str(notif.id),
            "type": notif.type.value,
            "channel": notif.channel.value,
            "status": notif.status,
            "sent_at": notif.sent_at.isoformat() if notif.sent_at else None,
            "payload": notif.payload,
            "created_at": notif.created_at.isoformat() if notif.created_at else None
        }
        for notif in notifications
    ]

