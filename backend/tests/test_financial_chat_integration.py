"""Integration test against disposable PostgreSQL, never production."""
import os
import sys
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
from datetime import date

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
if os.getenv("FINANCIAL_CHAT_TEST_DB") != "1":
    raise unittest.SkipTest("Requires an explicitly enabled disposable PostgreSQL instance.")
if "@127.0.0.1:" not in os.getenv("DATABASE_URL", ""):
    raise RuntimeError("Integration tests require local PostgreSQL.")

from app.db.database import Base, SessionLocal, engine
from app.db.models import User, Bill, BillStatus, BillType, Payment, SavingsGoal
from app.services.financial_chat_service import FinancialPlanItem, handle_financial_chat, monthly_financial_overview, read_history


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

    def chat(self, message, **kwargs):
        return handle_financial_chat(message, self.user, self.db, **kwargs)

    def bills(self):
        return self.db.query(Bill).filter_by(user_id=self.uid).all()

    def plans(self):
        return self.db.query(FinancialPlanItem).filter_by(user_id=self.uid).all()

    def test_confirmation_and_duplicate(self):
        message = "Gastei R$ 35 no Uber hoje\nAcademia: R$ 150/mês, paga pelo meu pai\nReserva: R$ 400/mês"
        self.assertEqual(self.chat(message)["action"], "confirm_transactions")
        self.assertEqual(len(self.bills()), 0)
        self.assertEqual(len(self.plans()), 0)
        confirmation_id = uuid.uuid4()
        self.assertEqual(self.chat("confirmar lançamentos", request_id=confirmation_id)["action"], "transactions_created")
        self.assertEqual(len(self.bills()), 1)
        self.assertEqual(self.bills()[0].status, BillStatus.PAID)
        self.assertEqual(self.bills()[0].amount, 35)
        self.assertEqual(len(self.plans()), 2)
        self.assertIn("R$ 150,00", self.chat("Meu planejamento mensal")["response"])
        self.assertEqual(self.chat("confirmar lançamentos", request_id=confirmation_id)["action"], "transactions_created")
        self.assertEqual(len(self.bills()), 1)
        self.chat(message)
        self.chat("confirmar lançamentos")
        self.assertEqual(len(self.bills()), 2)
        self.assertEqual(len(self.plans()), 4)

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

    def test_followup_correction_and_shared_state(self):
        self.assertIn("Com o que", self.chat("Gastei 150")["response"])
        self.assertIn("Em que dia", self.chat("Mercado")["response"])
        first = self.chat("Ontem")
        self.assertEqual(first["action"], "confirm_transactions")
        self.assertEqual(read_history(self.db, self.uid)["draft"]["draft_id"], first["draft_id"])
        result = self.chat("Corrija o item 1 para R$ 45")
        self.assertIn("R$ 45,00", result["response"])
        from fastapi import HTTPException
        with self.assertRaises(HTTPException):
            self.chat("sim", expected_draft=first["draft_id"])
        self.db.rollback()
        self.assertEqual(len(self.bills()), 0)
        self.chat("Pode colocar tudo", expected_draft=result["draft_id"])
        self.assertEqual(self.bills()[0].due_date, date(2026, 11, 24))
        self.assertEqual(self.bills()[0].amount, 45)

    def test_installments_payments_and_goals_use_existing_records(self):
        self.assertIn("primeiro vencimento", self.chat("Comprei uma cadeira de R$ 600,01 em 6x")["response"])
        self.chat("30/11/2026")
        self.chat("sim")
        bills = sorted(self.bills(), key=lambda bill: bill.due_date)
        self.assertEqual(len(bills), 6)
        self.assertEqual(sum(round(bill.amount * 100) for bill in bills), 60001)
        self.assertEqual(len({bill.installment_group_id for bill in bills}), 1)
        self.assertIsNotNone(bills[0].installment_group_id)
        self.assertEqual(bills[3].due_date, date(2027, 2, 28))
        self.assertEqual(monthly_financial_overview(self.db, self.uid, "2026-11")["actual"]["balance"], 0)
        self.assertEqual(self.chat(f"Paguei {bills[0].id} ontem")["action"], "confirm_transactions")
        self.chat("sim")
        self.assertEqual(self.db.query(Payment).filter_by(user_id=self.uid).one().executed_date, date(2026, 11, 24))
        self.assertEqual(monthly_financial_overview(self.db, self.uid, "2026-11")["actual"]["balance"], -10001)
        self.chat("Meta viagem: R$ 2.000")
        self.chat("sim")
        goal = self.db.query(SavingsGoal).filter_by(user_id=self.uid).one()
        self.assertEqual(goal.target_amount, 2000)
        self.assertEqual(goal.current_amount, 0)
        self.assertIsNone(goal.deadline)

    def test_summary_simulation_and_payment_links(self):
        self.chat("Mercado: R$ 100 todo mês\nAcademia: R$ 140, meu pai pagou ontem\nRecebi 2 mil do trabalho")
        self.assertEqual(self.chat("sim")["action"], "transactions_created")
        self.assertIn("Simulação", self.chat("Se eu gastar R$ 500, quanto vai sobrar?")["response"])
        self.assertIsNone(read_history(self.db, self.uid)["draft"])
        self.assertIn("R$ 140,00", self.chat("Quanto meu pai paga por mim?")["response"])
        self.assertIn("Diferença", self.chat("Quanto gastei em relação ao mês passado?")["response"])
        self.assertIn("vinculado", self.chat("Gastei R$ 100 no Mercado ontem")["response"])
        self.chat("sim")
        overview = monthly_financial_overview(self.db, self.uid, "2026-11")
        self.assertEqual(overview["actual"]["expense"], 10000)
        self.assertEqual(overview["actual"]["third"], 14000)
        self.assertEqual(overview["actual"]["income"], 200000)
        self.assertEqual(overview["planned"]["expense"], 0)
        self.assertEqual(monthly_financial_overview(self.db, self.uid, "2026-12")["planned"]["expense"], 10000)
        self.assertIn("100,00", self.chat("Quanto gastei com alimentação?")["response"])
        self.assertIn("Nenhum gasto", self.chat("E em dezembro?")["response"])

    def test_edit_and_delete_confirmations(self):
        self.chat("Gastei R$ 35 no Mercado ontem")
        self.chat("sim")
        self.assertEqual(self.chat("Edite Mercado para R$ 45")["action"], "confirm_transactions")
        self.assertEqual(self.bills()[0].amount, 35)
        self.chat("sim")
        self.assertEqual(self.bills()[0].amount, 45)
        self.assertEqual(self.chat("Exclua Mercado")["action"], "confirm_transactions")
        self.assertEqual(len(self.bills()), 1)
        self.chat("sim")
        self.assertEqual(len(self.bills()), 0)

    def test_concurrent_confirmation_with_same_request_id(self):
        draft = self.chat("Gastei R$ 35 no Mercado ontem")
        request_id = uuid.uuid4()

        def confirm():
            with SessionLocal() as session:
                user = session.get(User, self.uid)
                return handle_financial_chat("sim", user, session, request_id, draft["draft_id"])

        with ThreadPoolExecutor(max_workers=2) as workers:
            a, b = [workers.submit(confirm) for _ in range(2)]
            self.assertEqual(a.result(), b.result())
        self.assertEqual(len(self.bills()), 1)

    def test_forecast_vencimentos_do_not_create_personal_charges(self):
        self.chat("Academia: R$ 100 mensal a partir de 26/11/2026")
        self.chat("sim")
        self.assertEqual(len(self.bills()), 0)
        self.assertIn("Compromissos previstos", self.chat("Quais contas vencem amanhã?")["response"])
        overview = monthly_financial_overview(self.db, self.uid, "2026-12")
        self.assertEqual(overview["activity"]["planned_due"][0]["day"], "2026-12-26")
        self.assertEqual(overview["actual"]["pending"], 0)

    def test_confirming_boleto_data_does_not_mark_it_as_paid(self):
        for is_bill in (True, False):
            self.db.add(Bill(user_id=self.uid, is_bill=is_bill, due_date=date(2026, 11, 24),
                             type=BillType.EXPENSE, status=BillStatus.CONFIRMED, amount=50))
        self.db.commit()
        overview = monthly_financial_overview(self.db, self.uid, "2026-11")
        self.assertEqual(overview["actual"]["expense"], 5000)
        self.assertEqual(overview["actual"]["pending"], 5000)


if __name__ == "__main__":
    unittest.main()
