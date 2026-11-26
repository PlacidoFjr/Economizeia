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
        message = "Gastei R$ 35 no Uber hoje\nAcademia: R$ 150/mês previsto, paga pelo meu pai\nReserva: R$ 400/mês"
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
        result = self.chat("Mercado: R$ 100/mês previsto\nR$ 400 previstos para fim de semana")
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
        self.chat("Mercado: R$ 100 previsto todo mês\nAcademia: R$ 140, meu pai pagou ontem\nRecebi 2 mil do trabalho")
        self.assertEqual(self.chat("sim")["action"], "transactions_created")
        self.assertIn("Simulação", self.chat("Se eu gastar R$ 500, quanto vai sobrar?")["response"])
        self.assertIsNone(read_history(self.db, self.uid)["draft"])
        self.assertIn("R$ 140,00", self.chat("Quanto meu pai paga por mim?")["response"])
        self.assertIn("Diferença", self.chat("Quanto gastei em relação ao mês passado?")["response"])
        self.assertEqual(self.chat("Gastei R$ 100 no Mercado ontem")["action"], "confirm_transactions")
        self.chat("sim")
        overview = monthly_financial_overview(self.db, self.uid, "2026-11")
        self.assertEqual(overview["actual"]["expense"], 10000)
        self.assertEqual(overview["actual"]["third"], 14000)
        self.assertEqual(overview["actual"]["income"], 200000)
        self.assertEqual(overview["planned"]["expense"], 10000)
        self.assertEqual(monthly_financial_overview(self.db, self.uid, "2026-12")["planned"]["expense"], 10000)
        self.assertIn("100,00", self.chat("Quanto gastei com alimentação?")["response"])
        self.assertIn("Nenhum gasto", self.chat("E em dezembro?")["response"])

    def test_deposited_monthly_salary_realizes_existing_forecast_once(self):
        self.chat("Salário visão: R$ 2.000 previstos por mês")
        self.chat("sim")
        draft = self.chat("Salario depositado visão 2000 mensal")
        self.assertEqual(draft["action"], "confirm_transactions")
        self.assertIn("realizado", draft["response"])
        self.assertIn("vinculado", draft["response"])
        self.assertEqual(len(self.bills()), 0)
        self.chat("confirmar", expected_draft=draft["draft_id"])

        self.assertEqual(len(self.plans()), 1)
        self.assertEqual(len(self.bills()), 1)
        self.assertEqual(self.bills()[0].status, BillStatus.PAID)
        overview = monthly_financial_overview(self.db, self.uid, "2026-11")
        self.assertEqual(overview["actual"]["income"], 200000)
        self.assertEqual(overview["actual"]["balance"], 200000)
        self.assertEqual(overview["planned"]["income"], 0)
        self.assertEqual(monthly_financial_overview(self.db, self.uid, "2026-12")["planned"]["income"], 200000)

    def test_edit_plan_api_updates_dashboard_and_checks_ownership(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.api.v1.chatbot import router
        from app.core.security import create_access_token

        self.chat("Salário visão: R$ 2.000 previstos por mês")
        self.chat("sim")
        self.chat("Salario depositado visão 2000 mensal")
        self.chat("sim")
        self.chat("Limite lazer: R$ 200 previsto mensal em dezembro")
        self.chat("sim")

        app = FastAPI()
        app.include_router(router)
        auth = {"Authorization": "Bearer " + create_access_token({"sub": str(self.uid)})}
        with TestClient(app) as client:
            self.assertEqual(client.get("/plan-items").status_code, 403)
            items = client.get("/plan-items", headers=auth).json()
            income = next(item for item in items if item["kind"] == "income")
            budget = next(item for item in items if item["kind"] == "budget")
            self.assertEqual(budget["month"], "2026-12")

            income_id = income.pop("id")
            income.pop("shared")
            income.update(name="Novo salário", amount_cents=230000, account="Conta principal")
            url = "/plan-items/" + income_id
            saved = client.put(url, json=income, headers=auth)
            self.assertEqual(saved.status_code, 200, saved.text)
            self.assertEqual(client.put(url, json=income, headers=auth).status_code, 409)
            missing = client.put("/plan-items/" + str(uuid.uuid4()), json=income, headers=auth)
            self.assertEqual(missing.status_code, 404)
            other = User(id=uuid.uuid4(), name="Other", email=f"{uuid.uuid4()}@example.invalid",
                         password_hash="test-only", email_verified=True, is_active=True)
            self.db.add(other)
            self.db.commit()
            outsider = {"Authorization": "Bearer " + create_access_token({"sub": str(other.id)})}
            self.assertEqual(client.get("/plan-items", headers=outsider).json(), [])
            self.assertEqual(client.delete(url, headers=outsider, params={"version": saved.json()["version"]}).status_code, 404)

            november = client.get("/overview?month=2026-11", headers=auth).json()
            december = client.get("/overview?month=2026-12", headers=auth).json()
            self.assertEqual(november["actual"]["balance"], 200000)
            self.assertEqual(november["planned"]["income"], 0)
            self.assertEqual(december["planned"]["income"], 230000)
            deleted = client.delete(url, headers=auth, params={"version": saved.json()["version"]})
            self.assertEqual(deleted.status_code, 204)
            self.assertEqual(client.get("/overview?month=2026-12", headers=auth).json()["planned"]["income"], 0)
        self.assertEqual(len(self.bills()), 1)

    def test_edit_and_delete_generated_legacy_series_keeps_payment_history(self):
        from app.services.financial_plan_editor import PlanEdit, delete_item, serialize_plan, update_item

        self.chat("Curso: R$ 150 previsto mensal a partir de 25/11/2026 durante 3 meses")
        self.chat("sim")
        plan = self.plans()[0]
        plan.data = {key: value for key, value in plan.data.items() if key != "generated_bill_ids"}
        bill = next(bill for bill in self.bills() if bill.due_date.month == 11)
        bill.status = BillStatus.PAID
        self.db.commit()

        current = serialize_plan(plan)
        current.pop("id")
        current.pop("shared")
        current.update(amount_cents=17500, months=2)
        saved = update_item(self.db, self.uid, plan.id, PlanEdit(**current), date(2026, 11, 25))
        paid, upcoming = sorted(self.bills(), key=lambda bill: bill.due_date)
        self.assertEqual(paid.amount, 150)
        self.assertEqual(upcoming.amount, 175)
        self.assertEqual(upcoming.due_date.month, 12)
        delete_item(self.db, self.uid, plan.id, saved["version"])
        self.assertEqual(len(self.bills()), 1)
        self.assertEqual(self.bills()[0].status, BillStatus.PAID)


    def test_original_batch_and_transport_references(self):
        from app.services.financial_chat_parser import interpret
        message = "5.90 de passagem salvador card 25-11\n9,95 mercado 25-11\n6.10 uber moto 25-11\ndespesas"
        parsed, issues = interpret(message, date(2026, 11, 26))
        self.assertFalse(issues)
        self.assertEqual([item.amount_cents for item in parsed], [590, 995, 610])
        self.assertTrue(all(item.day == "2026-11-25" for item in parsed))
        self.chat("Ônibus e metrô: R$ 100 previstos mensal\nUber/moto: R$ 60 previstos mensal")
        self.chat("sim")
        draft = self.chat(message)
        self.assertEqual(draft["action"], "confirm_transactions")
        result = self.chat("sim")
        self.assertIn("R$ 21,95", result["response"])
        overview = monthly_financial_overview(self.db, self.uid, "2026-11")
        transport = next(group for group in overview["spending"] if group["category"] == "transporte")
        self.assertEqual((transport["planned"], transport["actual"], transport["remaining"], transport["percent"]), (16000,1200,14800,7.5))
        self.assertEqual({row["name"]: row["actual"] for row in transport["items"]}, {"Ônibus e metrô": 590, "Uber/moto": 610})
        self.chat("gastei 18,50 na 99 ontem")
        self.chat("sim")
        transport = next(group for group in monthly_financial_overview(self.db, self.uid, "2026-11")["spending"] if group["category"] == "transporte")
        self.assertEqual(transport["actual"], 3050)
        self.assertEqual(next(row for row in transport["items"] if row["name"] == "Uber/moto")["actual"], 2460)
        self.assertEqual(next(group for group in monthly_financial_overview(self.db, self.uid, "2026-12")["spending"] if group["category"] == "transporte")["actual"], 0)
        self.chat("Gastei R$ 200 de Uber ontem")
        self.chat("sim")
        transport = next(group for group in monthly_financial_overview(self.db, self.uid, "2026-11")["spending"] if group["category"] == "transporte")
        self.assertEqual(transport["remaining"], -7050)
        self.chat("Transporte: limite de R$ 150 por mês")
        self.chat("sim")
        transport = next(group for group in monthly_financial_overview(self.db, self.uid, "2026-11")["spending"] if group["category"] == "transporte")
        self.assertEqual(transport["planned"], 15000)



    def test_ambiguous_reference_and_manual_correction(self):
        from app.api.v1.chatbot import SpendingLink, update_spending_link
        self.chat("Transporte trabalho: R$ 100 previstos por mês\nTransporte pessoal: R$ 60 previstos por mês")
        self.chat("sim")
        draft = self.chat("Gastei R$ 25 de transporte ontem")
        self.assertIn("Escolha a referência", draft["response"])
        self.chat("sim")
        self.assertEqual(len(self.bills()), 0)
        self.chat("Vincule item 1 a Transporte trabalho")
        self.chat("sim")
        bill = self.bills()[0]
        self.assertIsNotNone(bill.expense_plan_id)
        other = next(row for row in self.plans() if row.data["name"] == "Transporte pessoal")
        update_spending_link(bill.id, SpendingLink(category="transporte", plan_id=other.id), self.user, self.db)
        overview = monthly_financial_overview(self.db, self.uid, "2026-11")
        row = next(group for group in overview["spending"] if group["category"] == "transporte")
        self.assertEqual(next(item for item in row["items"] if item["id"] == str(other.id))["actual"], 2500)
        self.chat("Edite transporte para R$ 30")
        self.chat("sim")
        self.assertEqual(next(group for group in monthly_financial_overview(self.db, self.uid, "2026-11")["spending"] if group["category"] == "transporte")["actual"], 3000)
        self.chat("Exclua transporte")
        self.chat("sim")
        self.assertEqual(next(group for group in monthly_financial_overview(self.db, self.uid, "2026-11")["spending"] if group["category"] == "transporte")["actual"], 0)


    def test_third_party_dashboard_reuses_plans_and_does_not_change_personal_balance(self):
        from app.services.third_party_expenses import (
            ThirdPartyEntry, ThirdPartyLimit, ThirdPartyFunding, third_party_overview,
            add_third_party_entry, set_card_limit, set_funding,
        )
        self.chat("Academia: R$ 150 por mês previsto, paga pelo meu pai")
        self.chat("sim")
        month = "2026-11"
        before = third_party_overview(self.db, self.user, month)
        self.assertEqual(before["planned_cents"], 15000)
        self.assertEqual(before["card_planned_cents"], 0)
        self.assertIsNone(before["limit_cents"])
        plan = before["planned"][0]
        set_funding(self.db, self.user, uuid.UUID(plan["id"]), ThirdPartyFunding(version=plan["version"], father_card=True))
        set_card_limit(self.db, self.user, month, ThirdPartyLimit(amount_cents=50000))
        entry = ThirdPartyEntry(request_id=uuid.uuid4(), name="Compra exemplo", amount_cents=1234, day=date(2026, 11, 25))
        with patch("app.services.third_party_expenses.user_today", return_value=date(2026, 11, 25)):
            add_third_party_entry(self.db, self.user, entry)
            result = add_third_party_entry(self.db, self.user, entry)
        self.assertEqual(len(self.bills()), 0)
        self.assertEqual(len(self.plans()), 2)
        self.assertEqual(result["card_spent_cents"], 1234)
        self.assertEqual(result["card_remaining_cents"], 48766)
        self.assertEqual(result["card_planned_cents"], 15000)
        self.assertEqual(result["actual_cents"], 1234)
        self.assertEqual(monthly_financial_overview(self.db, self.uid, month)["actual"]["balance"], 0)
        self.assertEqual(monthly_financial_overview(self.db, self.uid, month)["actual"]["third"], 1234)
        self.assertEqual(third_party_overview(self.db, self.user, "2026-12")["card_planned_cents"], 15000)
        self.assertEqual(third_party_overview(self.db, self.user, "2026-12")["actual_cents"], 0)
        self.chat("Gastei R$ 20 no cartão do meu pai hoje")
        self.assertEqual(self.chat("sim")["action"], "transactions_created")
        self.assertEqual(third_party_overview(self.db, self.user, month)["card_spent_cents"], 3234)
        self.assertEqual(len(self.bills()), 0)
        other = User(id=uuid.uuid4(), name="Other", email=f"{uuid.uuid4()}@example.invalid",
                     password_hash="test-only", email_verified=True, is_active=True, notif_prefs={})
        self.db.add(other)
        self.db.commit()
        self.assertEqual(third_party_overview(self.db, other, month)["actual_cents"], 0)
        self.assertIsNone(third_party_overview(self.db, other, month)["limit_cents"])
        from fastapi import HTTPException
        with self.assertRaises(HTTPException):
            set_funding(self.db, other, uuid.UUID(plan["id"]), ThirdPartyFunding(version=plan["version"], father_card=False))
        self.db.rollback()

    def test_production_varchar_enums_read_write_and_filter(self):
        from sqlalchemy import inspect, text
        from app.db.enum_compatibility import normalize_legacy_enum_labels

        # Match Neon production rather than creating an artificial native enum.
        columns = {column["name"]: column["type"] for column in inspect(engine).get_columns("bills")}
        self.assertEqual(str(columns["status"]), "VARCHAR(20)")
        self.assertEqual(str(columns["type"]), "VARCHAR(20)")
        expense_id, income_id = uuid.uuid4(), uuid.uuid4()
        with engine.begin() as conn:
            conn.execute(text(
                "INSERT INTO bills (id, user_id, issuer, amount, due_date, status, type, is_bill) "
                "VALUES (:id, :uid, 'Legacy expense', 12, '2026-11-25', 'paid', 'expense', false)"
            ), {"id": expense_id, "uid": self.uid})
        # Lowercase rows must be readable even without a migration/restart.
        self.assertEqual(self.db.get(Bill, expense_id).status, BillStatus.PAID)
        self.assertEqual(monthly_financial_overview(self.db, self.uid, "2026-11")["actual"]["expense"], 1200)
        with engine.begin() as conn:
            conn.execute(text(
                "INSERT INTO bills (id, user_id, issuer, amount, due_date, status, type, is_bill) "
                "VALUES (:id, :uid, 'Legacy income', 200, '2026-11-25', 'PAID', 'INCOME', false)"
            ), {"id": income_id, "uid": self.uid})
        normalize_legacy_enum_labels(engine, Base.metadata)
        self.assertEqual(normalize_legacy_enum_labels(engine, Base.metadata), 0)
        self.db.expire_all()
        self.assertEqual(self.db.get(Bill, income_id).type, BillType.INCOME)
        self.assertEqual(self.db.query(Bill).filter_by(user_id=self.uid, status=BillStatus.PAID).count(), 2)
        overview = monthly_financial_overview(self.db, self.uid, "2026-11")
        self.assertEqual(overview["actual"]["income"], 20000)
        self.assertEqual(overview["actual"]["expense"], 1200)
        self.assertEqual(overview["actual"]["balance"], 18800)
        draft = self.chat("Gastei R$ 5 no Uber ontem")
        self.assertEqual(draft["action"], "confirm_transactions")
        self.chat("sim", expected_draft=draft["draft_id"])
        with engine.connect() as conn:
            labels = conn.execute(text(
                "SELECT status, type FROM bills WHERE user_id = :uid ORDER BY amount"
            ), {"uid": self.uid}).all()
        self.assertEqual(labels, [("paid", "expense"), ("paid", "expense"), ("paid", "income")])
        self.assertEqual(monthly_financial_overview(self.db, self.uid, "2026-11")["actual"]["balance"], 18300)

    def test_quick_entry_is_confirmed_and_preserves_selected_type(self):
        entry = {"kind": "expense", "name": "Reserva de hotel", "amount_cents": 12590, "day": "2026-11-25"}
        request_id = uuid.uuid4()
        draft = self.chat("Gasto extra: Reserva de hotel", request_id=request_id, entry=entry)
        self.assertEqual(draft["action"], "confirm_transactions")
        self.assertIn("Despesa", draft["response"])
        self.assertEqual(len(self.bills()), 0)
        self.assertEqual(self.chat("Gasto extra: Reserva de hotel", request_id=request_id, entry=entry), draft)
        self.chat("sim", expected_draft=draft["draft_id"])
        self.assertEqual(len(self.bills()), 1)
        self.assertEqual(self.bills()[0].amount, 125.9)
        income = dict(entry, kind="income", name="Venda")
        second = self.chat("Receita: Venda", entry=income)
        self.chat("sim", expected_draft=second["draft_id"])
        self.assertEqual(len(self.bills()), 2)
        self.assertEqual(monthly_financial_overview(self.db, self.uid, "2026-11")["actual"]["balance"], 0)

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
