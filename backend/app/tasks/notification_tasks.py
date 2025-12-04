from celery import shared_task
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import User, Bill, BillStatus, BillType
from app.services.notification_service import notification_service
import logging
from uuid import UUID
from datetime import datetime, date, timedelta
from typing import List, Dict

logger = logging.getLogger(__name__)


@shared_task(name="schedule_reminder_task")
def schedule_reminder_task(user_id: str, bill_id: str, issuer: str, amount: float, 
                          due_date_str: str, days_before: int):
    """
    Send reminder notification for a bill.
    """
    db: Session = SessionLocal()
    
    try:
        user = db.query(User).filter(User.id == UUID(user_id)).first()
        bill = db.query(Bill).filter(Bill.id == UUID(bill_id)).first()
        
        if not user or not bill:
            logger.error(f"User or bill not found: {user_id}, {bill_id}")
            return
        
        due_date = datetime.fromisoformat(due_date_str).date()
        
        # Send reminder
        import asyncio
        asyncio.run(
            notification_service.send_bill_reminder(
                db=db,
                user=user,
                bill_id=bill.id,
                issuer=issuer,
                amount=amount,
                due_date=due_date,
                days_before=days_before
            )
        )
        
        logger.info(f"Sent reminder for bill {bill_id} to user {user_id}, {days_before} days before")
        
    except Exception as e:
        logger.error(f"Error sending reminder: {e}", exc_info=True)
    finally:
        db.close()


@shared_task(name="check_budget_alerts")
def check_budget_alerts():
    """Check all users for budget exceeded alerts (runs daily)."""
    db: Session = SessionLocal()
    
    try:
        users = db.query(User).filter(User.is_active == True, User.email_verified == True).all()
        today = date.today()
        current_month = today.month
        current_year = today.year
        
        for user in users:
            try:
                # Get all bills for current month
                user_bills = db.query(Bill).filter(
                    Bill.user_id == user.id,
                    Bill.due_date.isnot(None)
                ).all()
                
                # Calculate monthly income and expenses
                monthly_income = sum(
                    b.amount for b in user_bills
                    if b.due_date and b.due_date.month == current_month and b.due_date.year == current_year
                    and b.type == BillType.INCOME and b.status in [BillStatus.PAID, BillStatus.CONFIRMED]
                ) or 0.0
                
                monthly_expenses = sum(
                    b.amount for b in user_bills
                    if b.due_date and b.due_date.month == current_month and b.due_date.year == current_year
                    and b.type == BillType.EXPENSE and b.status in [BillStatus.PAID, BillStatus.CONFIRMED]
                ) or 0.0
                
                monthly_balance = monthly_income - monthly_expenses
                
                # Check if expenses exceed income
                if monthly_income > 0 and monthly_expenses > monthly_income:
                    percentage_over = ((monthly_expenses - monthly_income) / monthly_income) * 100
                    
                    # Check if we already sent this alert today
                    from app.db.models import Notification, NotificationType
                    today_start = datetime.combine(today, datetime.min.time())
                    recent_alert = db.query(Notification).filter(
                        Notification.user_id == user.id,
                        Notification.type == NotificationType.ANOMALY,
                        Notification.sent_at >= today_start
                    ).first()
                    
                    if not recent_alert:
                        import asyncio
                        asyncio.run(
                            notification_service.send_budget_exceeded_alert(
                                db=db,
                                user=user,
                                monthly_income=monthly_income,
                                monthly_expenses=monthly_expenses,
                                monthly_balance=monthly_balance,
                                percentage_over=percentage_over
                            )
                        )
                        logger.info(f"Sent budget exceeded alert to user {user.id}")
                        
            except Exception as e:
                logger.error(f"Error checking budget for user {user.id}: {e}", exc_info=True)
                continue
                
    except Exception as e:
        logger.error(f"Error in check_budget_alerts: {e}", exc_info=True)
    finally:
        db.close()


@shared_task(name="check_upcoming_payments")
def check_upcoming_payments():
    """Check all users for upcoming payments (runs daily)."""
    db: Session = SessionLocal()
    
    try:
        users = db.query(User).filter(User.is_active == True, User.email_verified == True).all()
        today = date.today()
        
        for user in users:
            try:
                # Get upcoming bills (next 7 days)
                upcoming_bills_query = db.query(Bill).filter(
                    Bill.user_id == user.id,
                    Bill.status.in_([BillStatus.PENDING, BillStatus.CONFIRMED, BillStatus.SCHEDULED]),
                    Bill.due_date.isnot(None),
                    Bill.due_date >= today,
                    Bill.due_date <= today + timedelta(days=7)
                ).order_by(Bill.due_date).all()
                
                if not upcoming_bills_query:
                    continue
                
                upcoming_bills: List[Dict] = []
                for bill in upcoming_bills_query:
                    days_until = (bill.due_date - today).days
                    upcoming_bills.append({
                        "issuer": bill.issuer or "Desconhecido",
                        "amount": float(bill.amount),
                        "due_date": bill.due_date.isoformat() if bill.due_date else None,
                        "days_until": days_until,
                        "bill_id": str(bill.id)
                    })
                
                # Check if we already sent this alert today
                from app.db.models import Notification, NotificationType
                today_start = datetime.combine(today, datetime.min.time())
                recent_alert = db.query(Notification).filter(
                    Notification.user_id == user.id,
                    Notification.type == NotificationType.REMINDER,
                    Notification.sent_at >= today_start
                ).first()
                
                if not recent_alert and upcoming_bills:
                    import asyncio
                    asyncio.run(
                        notification_service.send_upcoming_payments_alert(
                            db=db,
                            user=user,
                            upcoming_bills=upcoming_bills
                        )
                    )
                    logger.info(f"Sent upcoming payments alert to user {user.id} ({len(upcoming_bills)} bills)")
                    
            except Exception as e:
                logger.error(f"Error checking upcoming payments for user {user.id}: {e}", exc_info=True)
                continue
                
    except Exception as e:
        logger.error(f"Error in check_upcoming_payments: {e}", exc_info=True)
    finally:
        db.close()

