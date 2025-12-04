"""
Script para popular banco de dados com dados sintéticos para testes.
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import User, Bill, BillDocument, BillStatus, Account, Payment, PaymentMethod, PaymentStatus
from app.core.security import get_password_hash
from datetime import date, timedelta
import uuid
import random

# Dados sintéticos
ISSUERS = [
    "Energia Elétrica",
    "Água e Saneamento",
    "Internet/Telefone",
    "Supermercado",
    "Farmácia",
    "Combustível",
    "Seguro Auto",
    "Plano de Saúde",
    "Faculdade",
    "Cartão de Crédito"
]

AMOUNTS = [50.00, 75.50, 120.00, 150.00, 200.00, 250.00, 300.00, 450.00, 500.00, 750.00, 1000.00]


def create_test_user(db: Session) -> User:
    """Create a test user."""
    # Verificar se já existe
    existing_user = db.query(User).filter(User.email == "teste@finguia.com").first()
    if existing_user:
        print(f"Usuário de teste já existe: {existing_user.email}")
        return existing_user
    
    user = User(
        id=uuid.uuid4(),
        name="Usuário Teste",
        email="teste@finguia.com",
        password_hash=get_password_hash("senha123"),
        phone="+5511999999999",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_test_accounts(db: Session, user: User):
    """Create test accounts."""
    accounts = [
        Account(
            id=uuid.uuid4(),
            user_id=user.id,
            name="Conta Corrente",
            type="checking",
            estimated_balance=5000.00
        ),
        Account(
            id=uuid.uuid4(),
            user_id=user.id,
            name="Poupança",
            type="savings",
            estimated_balance=10000.00
        )
    ]
    for account in accounts:
        db.add(account)
    db.commit()


def create_test_bills(db: Session, user: User, count: int = 20):
    """Create test bills."""
    bills = []
    today = date.today()
    
    for i in range(count):
        due_date = today + timedelta(days=random.randint(-10, 30))
        amount = random.choice(AMOUNTS)
        issuer = random.choice(ISSUERS)
        confidence = random.uniform(0.6, 1.0)
        
        bill = Bill(
            id=uuid.uuid4(),
            user_id=user.id,
            issuer=issuer,
            amount=amount,
            currency="BRL",
            due_date=due_date,
            barcode=f"34191.09008 01234.567890 12345.678901 2 {random.randint(10000000000, 99999999999)}",
            status=BillStatus.CONFIRMED if confidence >= 0.9 else BillStatus.PENDING,
            confidence=confidence,
            category=random.choice(["alimentacao", "moradia", "servicos", "transporte", "saude", "outras"])
        )
        db.add(bill)
        bills.append(bill)
        
        # Create document
        document = BillDocument(
            id=uuid.uuid4(),
            bill_id=bill.id,
            s3_path=f"bills/{user.id}/{bill.id}/boleto_{i}.pdf",
            ocr_text=f"Boleto de {issuer}\nValor: R$ {amount:.2f}\nVencimento: {due_date.isoformat()}",
            ocr_confidence=confidence,
            extracted_json={
                "issuer": issuer,
                "amount": amount,
                "due_date": due_date.isoformat(),
                "confidence": confidence
            }
        )
        db.add(document)
    
    db.commit()
    return bills


def create_test_payments(db: Session, user: User, bills: list):
    """Create test payments."""
    for bill in bills[:10]:  # Create payments for first 10 bills
        if bill.status == BillStatus.CONFIRMED:
            payment = Payment(
                id=uuid.uuid4(),
                bill_id=bill.id,
                user_id=user.id,
                scheduled_date=bill.due_date,
                executed_date=bill.due_date if random.random() > 0.3 else None,
                method=random.choice(list(PaymentMethod)),
                status=PaymentStatus.EXECUTED if bill.due_date < date.today() else PaymentStatus.SCHEDULED,
                notify_before_days=[7, 3, 1]
            )
            db.add(payment)
            if payment.status == PaymentStatus.EXECUTED:
                bill.status = BillStatus.PAID
    
    db.commit()


def main():
    """Main seed function."""
    db: Session = SessionLocal()
    
    try:
        print("Creating test user...")
        user = create_test_user(db)
        print(f"Created user: {user.email}")
        
        print("Creating test accounts...")
        create_test_accounts(db, user)
        print("Accounts created")
        
        print("Creating test bills...")
        bills = create_test_bills(db, user, count=20)
        print(f"Created {len(bills)} bills")
        
        print("Creating test payments...")
        create_test_payments(db, user, bills)
        print("Payments created")
        
        print("\nSeed completed successfully!")
        print(f"\nLogin credentials:")
        print(f"Email: {user.email}")
        print(f"Password: senha123")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

