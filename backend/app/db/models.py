from sqlalchemy import Column, String, Integer, Float, Date, DateTime, Boolean, Text, Enum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.db.database import Base


class BillStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SCHEDULED = "scheduled"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class BillType(str, enum.Enum):
    EXPENSE = "expense"  # Despesa
    INCOME = "income"    # Receita


class PaymentMethod(str, enum.Enum):
    PIX = "PIX"
    BOLETO = "BOLETO"
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"
    TRANSFER = "TRANSFER"


class PaymentStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    EXECUTED = "executed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationChannel(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class NotificationType(str, enum.Enum):
    REMINDER = "reminder"
    OVERDUE = "overdue"
    PAYMENT_CONFIRMED = "payment_confirmed"
    RECONCILIATION = "reconciliation"
    ANOMALY = "anomaly"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)
    email_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), nullable=True)
    verification_token_expires = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    notif_prefs = Column(JSONB, default={
        "email_enabled": True,
        "sms_enabled": False,
        "push_enabled": True,
        "reminder_days": [7, 3, 1]
    })

    # Relationships
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    bills = relationship("Bill", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class Account(Base):
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # checking, savings, credit
    estimated_balance = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="accounts")


class Bill(Base):
    __tablename__ = "bills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    issuer = Column(String(255), nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="BRL")
    due_date = Column(Date, nullable=False)
    barcode = Column(String(255), nullable=True)
    status = Column(Enum(BillStatus), default=BillStatus.PENDING)
    type = Column(Enum(BillType), default=BillType.EXPENSE)  # expense ou income
    is_bill = Column(Boolean, default=True)  # True se for boleto/documento, False se for transação manual
    confidence = Column(Float, default=0.0)
    category = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="bills")
    documents = relationship("BillDocument", back_populates="bill", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="bill", cascade="all, delete-orphan")


class BillDocument(Base):
    __tablename__ = "bill_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(UUID(as_uuid=True), ForeignKey("bills.id"), nullable=False)
    s3_path = Column(String(500), nullable=False)
    ocr_text = Column(Text, nullable=True)
    ocr_confidence = Column(Float, default=0.0)
    extracted_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    bill = relationship("Bill", back_populates="documents")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(UUID(as_uuid=True), ForeignKey("bills.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    scheduled_date = Column(Date, nullable=False)
    executed_date = Column(Date, nullable=True)
    method = Column(Enum(PaymentMethod), nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.SCHEDULED)
    comprovante_path = Column(String(500), nullable=True)
    notify_before_days = Column(JSONB, default=[7, 3, 1])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    bill = relationship("Bill", back_populates="payments")
    user = relationship("User", back_populates="payments")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    type = Column(Enum(NotificationType), nullable=False)
    channel = Column(Enum(NotificationChannel), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    payload = Column(JSONB, nullable=True)
    status = Column(String(50), default="pending")  # pending, sent, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="notifications")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity = Column(String(100), nullable=False)  # bill, payment, user, etc
    action = Column(String(50), nullable=False)  # create, update, delete, confirm, etc
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    details = Column(JSONB, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

