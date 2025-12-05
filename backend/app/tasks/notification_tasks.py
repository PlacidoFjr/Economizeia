from celery import shared_task  # type: ignore
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.database import SessionLocal
from app.db.models import User, Bill, BillStatus, BillType, SavingsGoal, SavingsGoalStatus, Notification, NotificationType
from app.services.notification_service import notification_service
import logging
from uuid import UUID
from datetime import datetime, date, timedelta
from typing import List, Dict
from collections import defaultdict

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
                        # Send spending alert
                        import asyncio
                        percentage_used = (monthly_expenses / monthly_income * 100) if monthly_income > 0 else 0
                        asyncio.run(
                            notification_service.send_spending_alert(
                                db=db,
                                user=user,
                                current_expenses=monthly_expenses,
                                monthly_income=monthly_income,
                                percentage_used=percentage_used
                            )
                        )
                        logger.info(f"✅ Sent spending alert to user {user.id} ({percentage_used:.1f}% used)")
                        
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


@shared_task(name="check_savings_goals_reminders")
def check_savings_goals_reminders():
    """Check all users for savings goals reminders (runs daily)."""
    db: Session = SessionLocal()
    
    try:
        users = db.query(User).filter(User.is_active == True, User.email_verified == True).all()
        today = date.today()
        
        for user in users:
            try:
                # Get active savings goals
                active_goals = db.query(SavingsGoal).filter(
                    SavingsGoal.user_id == user.id,
                    SavingsGoal.status == SavingsGoalStatus.ACTIVE,
                    SavingsGoal.deadline >= today
                ).all()
                
                if not active_goals:
                    continue
                
                for goal in active_goals:
                    days_remaining = (goal.deadline - today).days
                    notify_days = goal.notify_days_before or [30, 15, 7, 3, 1]
                    
                    # Check if we should send a reminder today
                    if days_remaining in notify_days:
                        # Check if we already sent a reminder for this goal today
                        today_start = datetime.combine(today, datetime.min.time())
                        recent_notifications = db.query(Notification).filter(
                            Notification.user_id == user.id,
                            Notification.type == NotificationType.SAVINGS_GOAL_REMINDER,
                            Notification.sent_at >= today_start
                        ).all()
                        
                        # Check if any notification is for this goal
                        recent_notification = None
                        for notif in recent_notifications:
                            if notif.payload and notif.payload.get('goal_name') == goal.name:
                                recent_notification = notif
                                break
                        
                        if not recent_notification:
                            import asyncio
                            asyncio.run(
                                notification_service.send_savings_goal_reminder(
                                    db=db,
                                    user=user,
                                    goal_name=goal.name,
                                    target_amount=goal.target_amount,
                                    current_amount=goal.current_amount,
                                    deadline=goal.deadline,
                                    days_remaining=days_remaining
                                )
                            )
                            goal.last_notification_sent = today
                            db.commit()
                            logger.info(f"Sent savings goal reminder to user {user.id} for goal '{goal.name}' ({days_remaining} days remaining)")
                    
                    # Check if deadline is approaching (within 1 day) and goal is not completed
                    if days_remaining <= 1 and goal.current_amount < goal.target_amount:
                        # Check if we already sent a deadline warning today
                        today_start = datetime.combine(today, datetime.min.time())
                        recent_deadline_notifications = db.query(Notification).filter(
                            Notification.user_id == user.id,
                            Notification.type == NotificationType.SAVINGS_GOAL_DEADLINE,
                            Notification.sent_at >= today_start
                        ).all()
                        
                        # Check if any notification is for this goal
                        recent_deadline_notification = None
                        for notif in recent_deadline_notifications:
                            if notif.payload and notif.payload.get('goal_name') == goal.name:
                                recent_deadline_notification = notif
                                break
                        
                        if not recent_deadline_notification:
                            import asyncio
                            asyncio.run(
                                notification_service.send_savings_goal_reminder(
                                    db=db,
                                    user=user,
                                    goal_name=goal.name,
                                    target_amount=goal.target_amount,
                                    current_amount=goal.current_amount,
                                    deadline=goal.deadline,
                                    days_remaining=days_remaining
                                )
                            )
                            goal.last_notification_sent = today
                            db.commit()
                            logger.info(f"Sent savings goal deadline warning to user {user.id} for goal '{goal.name}'")
                            
            except Exception as e:
                logger.error(f"Error checking savings goals for user {user.id}: {e}", exc_info=True)
                continue
                
    except Exception as e:
        logger.error(f"Error in check_savings_goals_reminders: {e}", exc_info=True)
    finally:
        db.close()


@shared_task(name="send_monthly_reports")
def send_monthly_reports():
    """Send monthly financial reports to all users (runs on the 1st of each month)."""
    db: Session = SessionLocal()
    
    try:
        today = date.today()
        
        # Calculate previous month
        if today.month == 1:
            report_month = 12
            report_year = today.year - 1
        else:
            report_month = today.month - 1
            report_year = today.year
        
        # Get all active and verified users
        users = db.query(User).filter(
            User.is_active == True,
            User.email_verified == True
        ).all()
        
        logger.info(f"📊 Sending monthly reports for {report_month}/{report_year} to {len(users)} users")
        
        for user in users:
            try:
                # Get all bills for the report month
                user_bills = db.query(Bill).filter(
                    Bill.user_id == user.id,
                    Bill.due_date.isnot(None),
                    func.extract('month', Bill.due_date) == report_month,
                    func.extract('year', Bill.due_date) == report_year
                ).all()
                
                # Calculate totals
                total_income = sum(
                    float(b.amount) for b in user_bills
                    if b.type == BillType.INCOME and b.status in [BillStatus.PAID, BillStatus.CONFIRMED]
                ) or 0.0
                
                total_expenses = sum(
                    float(b.amount) for b in user_bills
                    if b.type == BillType.EXPENSE and b.status in [BillStatus.PAID, BillStatus.CONFIRMED]
                ) or 0.0
                
                balance = total_income - total_expenses
                
                # Count bills by status
                bills_paid = len([b for b in user_bills if b.status == BillStatus.PAID])
                bills_pending = len([b for b in user_bills if b.status in [BillStatus.PENDING, BillStatus.CONFIRMED, BillStatus.SCHEDULED]])
                bills_overdue = len([b for b in user_bills if b.status == BillStatus.OVERDUE])
                
                # Top categories
                category_totals = defaultdict(float)
                for bill in user_bills:
                    if bill.type == BillType.EXPENSE and bill.category:
                        category_totals[bill.category] += float(bill.amount or 0)
                
                top_categories = [
                    {"name": cat, "total": total}
                    for cat, total in sorted(category_totals.items(), key=lambda x: x[1], reverse=True)[:5]
                ]
                
                # Savings goals progress
                active_goals = db.query(SavingsGoal).filter(
                    SavingsGoal.user_id == user.id,
                    SavingsGoal.status == SavingsGoalStatus.ACTIVE
                ).all()
                
                savings_goals_progress = [
                    {
                        "name": goal.name,
                        "current": float(goal.current_amount),
                        "target": float(goal.target_amount),
                        "progress": (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
                    }
                    for goal in active_goals[:3]
                ]
                
                # Comparison with previous month
                if report_month == 1:
                    prev_month = 12
                    prev_year = report_year - 1
                else:
                    prev_month = report_month - 1
                    prev_year = report_year
                
                prev_month_bills = db.query(Bill).filter(
                    Bill.user_id == user.id,
                    Bill.due_date.isnot(None),
                    func.extract('month', Bill.due_date) == prev_month,
                    func.extract('year', Bill.due_date) == prev_year
                ).all()
                
                prev_income = sum(
                    float(b.amount) for b in prev_month_bills
                    if b.type == BillType.INCOME and b.status in [BillStatus.PAID, BillStatus.CONFIRMED]
                ) or 0.0
                
                prev_expenses = sum(
                    float(b.amount) for b in prev_month_bills
                    if b.type == BillType.EXPENSE and b.status in [BillStatus.PAID, BillStatus.CONFIRMED]
                ) or 0.0
                
                income_change_percent = ((total_income - prev_income) / prev_income * 100) if prev_income > 0 else 0.0
                expenses_change_percent = ((total_expenses - prev_expenses) / prev_expenses * 100) if prev_expenses > 0 else 0.0
                
                comparison_previous = {
                    "income_change_percent": income_change_percent,
                    "expenses_change_percent": expenses_change_percent
                }
                
                # Check if we already sent this report (check last 7 days to avoid duplicates)
                check_start = today - timedelta(days=7)
                recent_report = db.query(Notification).filter(
                    Notification.user_id == user.id,
                    Notification.type == NotificationType.RECONCILIATION,
                    Notification.sent_at >= check_start
                ).first()
                
                if not recent_report:
                    monthly_data = {
                        "total_income": total_income,
                        "total_expenses": total_expenses,
                        "balance": balance,
                        "bills_paid": bills_paid,
                        "bills_pending": bills_pending,
                        "bills_overdue": bills_overdue,
                        "top_categories": top_categories,
                        "savings_goals_progress": savings_goals_progress,
                        "comparison_previous": comparison_previous
                    }
                    
                    import asyncio
                    sent = asyncio.run(
                        notification_service.send_monthly_report(
                            db=db,
                            user=user,
                            report_month=report_month,
                            report_year=report_year,
                            monthly_data=monthly_data
                        )
                    )
                    
                    if sent:
                        logger.info(f"✅ Sent monthly report to user {user.id} ({user.email}) for {report_month}/{report_year}")
                    else:
                        logger.warning(f"⚠️ Failed to send monthly report to user {user.id} ({user.email})")
                else:
                    logger.info(f"⏭️ Monthly report already sent to user {user.id} for {report_month}/{report_year}, skipping")
                    
            except Exception as e:
                logger.error(f"Error sending monthly report to user {user.id}: {e}", exc_info=True)
                continue
                
    except Exception as e:
        logger.error(f"Error in send_monthly_reports: {e}", exc_info=True)
    finally:
        db.close()

