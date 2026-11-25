"""Integration test against disposable PostgreSQL, never production."""
import os
import sys
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch
from datetime import date

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
if os.getenv("FINANCIAL_CHAT_TEST_DB") != "1":
    raise unittest.SkipTest("Requires an explicitly enabled disposable PostgreSQL instance.")
if "@127.0.0.1:" not in os.getenv("DATABASE_URL", ""):
    raise RuntimeError("Integration tests require local PostgreSQL.")

from app.db.database import Base, SessionLocal, engine
from app.db.models import User, Bill, BillStatus
from app.services.financial_chat_service import FinancialChatState, FinancialPlanItem, handle_financial_chat


class FinancialChatIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        self.db = SessionLocal()
        self.user = User(id=uuid.uuid4(), name="Example", email=f"{uuid.uuid4()}@example.invalid",
                         password_hash="test-only", email_verified=True, is_active=True, notif_prefs={})
        self.db.add(self.user)
        self.db.commit()
        self.uid = self.user.id
        self.clock = patch("app.services.financial_chat_service.today_local", return_value=date(2026, 11, 25))
        self.clock.start()

    def tearDown(self):
        self.clock.stop()
        self.db.close()

    def chat(self, message):
        return handle_financial_chat(message, self.user, self.db)

    def bills(self):
        return self.db.query(Bill).filter_by(user_id=self.uid).all()

    def plans(self):
        return self.db.query(FinancialPlanItem).filter_by(user_id=self.uid).all()

    def test_confirmation_and_duplicate(self):
        message = "Gastei R$ 35 no Uber hoje\nAcademia: R$ 150/mês, paga pelo meu pai\nReserva: R$ 400/mês"
        self.assertEqual(self.chat(message)["action"], "confirm_transactions")
        self.assertEqual(len(self.bills()), 0)
        self.assertEqual(len(self.plans()), 0)
        self.assertEqual(self.chat("confirmar lançamentos")["action"], "transactions_created")
        self.assertEqual(len(self.bills()), 1)
        self.assertEqual(self.bills()[0].status, BillStatus.PAID)
        self.assertEqual(self.bills()[0].amount, 35)
        self.assertEqual(len(self.plans()), 2)
        self.assertIn("R$ 150,00", self.chat("Meu planejamento mensal")["response"])
        self.chat("confirmar lançamentos")
        self.assertEqual(len(self.bills()), 1)
        self.chat(message)
        self.chat("confirmar lançamentos")
        self.assertEqual(len(self.bills()), 1)
        self.assertEqual(len(self.plans()), 2)

    def test_cancel_and_isolation(self):
        self.chat("Gastei R$ 25 no mercado hoje")
        self.chat("cancelar")
        self.chat("sim")
        self.assertEqual(len(self.bills()), 0)
        self.chat("Gastei R$ 25 no mercado hoje")
        other = User(id=uuid.uuid4(), name="Other", email=f"{uuid.uuid4()}@example.invalid",
                     password_hash="test-only", email_verified=True, is_active=True, notif_prefs={})
        self.db.add(other)
        self.db.commit()
        self.assertIn("Não existe rascunho", handle_financial_chat("sim", other, self.db)["response"])
        self.assertEqual(len(self.bills()), 0)
        self.chat("sim")
        self.assertEqual(len(self.bills()), 1)
        self.assertEqual(self.db.query(Bill).filter_by(user_id=other.id).count(), 0)

    def test_ambiguity_never_partially_saves(self):
        result = self.chat("Mercado: R$ 100/mês\nR$ 400 previstos para fim de semana")
        self.assertEqual(result["action"], "ask_for_info")
        self.chat("sim")
        self.assertEqual(len(self.plans()), 0)
        self.assertEqual(len(self.bills()), 0)


if __name__ == "__main__":
    unittest.main()
