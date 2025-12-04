"""
Script para enviar email de teste.
Uso: python scripts/send_test_email.py <email>
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.notification_service import notification_service
from app.db.database import SessionLocal
from app.db.models import User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def send_test_email(email: str):
    """Send test email to specified address."""
    db = SessionLocal()
    
    try:
        # Create a test user object (or use existing)
        test_user = db.query(User).filter(User.email == email).first()
        
        if not test_user:
            logger.warning(f"User {email} not found in database. Creating test user object...")
            from app.db.models import User as UserModel
            test_user = type('User', (), {
                'id': '00000000-0000-0000-0000-000000000000',
                'name': 'Usuário de Teste',
                'email': email,
                'notif_prefs': {'email_enabled': True}
            })()
        
        # Test 1: Budget exceeded alert
        logger.info("Sending budget exceeded alert test email...")
        sent1 = await notification_service.send_budget_exceeded_alert(
            db=db,
            user=test_user,
            monthly_income=5000.00,
            monthly_expenses=6500.00,
            monthly_balance=-1500.00,
            percentage_over=30.0
        )
        
        if sent1:
            logger.info("✅ Budget exceeded alert sent successfully!")
        else:
            logger.error("❌ Failed to send budget exceeded alert")
        
        # Wait a bit before next email
        await asyncio.sleep(2)
        
        # Test 2: Upcoming payments alert
        logger.info("Sending upcoming payments alert test email...")
        upcoming_bills = [
            {
                "issuer": "Energia Elétrica",
                "amount": 250.50,
                "due_date": "2025-12-06",
                "days_until": 2,
                "bill_id": "test-1"
            },
            {
                "issuer": "Internet",
                "amount": 99.90,
                "due_date": "2025-12-07",
                "days_until": 3,
                "bill_id": "test-2"
            },
            {
                "issuer": "Supermercado",
                "amount": 450.00,
                "due_date": "2025-12-10",
                "days_until": 6,
                "bill_id": "test-3"
            }
        ]
        
        sent2 = await notification_service.send_upcoming_payments_alert(
            db=db,
            user=test_user,
            upcoming_bills=upcoming_bills
        )
        
        if sent2:
            logger.info("✅ Upcoming payments alert sent successfully!")
        else:
            logger.error("❌ Failed to send upcoming payments alert")
        
        logger.info(f"\n📧 Test emails sent to {email}")
        logger.info("Check your inbox (and spam folder) for the test emails.")
        
    except Exception as e:
        logger.error(f"Error sending test email: {e}", exc_info=True)
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        email = "jujubazin12@gmail.com"
        logger.info(f"No email provided, using default: {email}")
    else:
        email = sys.argv[1]
    
    asyncio.run(send_test_email(email))

