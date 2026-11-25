import sys
import unittest
from dataclasses import asdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.financial_chat_parser import interpret, cents, plan_totals, occurs, item_key


class FinancialChatParserTests(unittest.TestCase):
    today = date(2026, 11, 25)

    def test_currency(self):
        self.assertEqual(cents("2.000,00"), 200000)
        self.assertEqual(cents("86,05"), 8605)
        self.assertEqual(cents("2.000"), 200000)
        self.assertEqual(cents("12.90"), 1290)
        with self.assertRaises(ValueError):
            cents("0")

    def test_monthly_plan(self):
        items, issues = interpret("""RECEITA
- Contrato PJ Empresa Exemplo: R$ 2.000,00 por mês, durante 6 meses.
- Conta de recebimento: Conta Exemplo PJ.
DESPESAS PAGAS POR MIM
- Moradia: R$ 40,00/mês.
- Ônibus e metrô: R$ 100,00/mês.
- Uber/moto: R$ 60,00/mês.
- Alimentação/proteínas: R$ 400,00/mês.
- DAS MEI: R$ 86,05/mês.
DESPESAS PAGAS PELO MEU PAI
- Academia: R$ 150,00/mês.
- Spotify: R$ 12,90/mês.
- YouTube: R$ 16,90/mês.
- Cinemark: R$ 32,99/mês.
ORÇAMENTO E METAS
- Lazer: limite de R$ 200,00/mês.
- Reserva financeira: guardar R$ 400,00/mês.
REGRAS IMPORTANTES
1. Não duplique lançamentos.""", self.today)
        self.assertFalse(issues, issues)
        self.assertEqual(len(items), 12)
        data = [asdict(i) for i in items]
        p = plan_totals(data, "2026-11")
        self.assertEqual(p["income"], 200000)
        self.assertEqual(p["expense"], 68605)
        self.assertEqual(p["third"], 21279)
        self.assertEqual(p["budget"], 20000)
        self.assertEqual(p["reserve"], 40000)
        self.assertEqual(p["income"] - p["expense"] - p["budget"] - p["reserve"], 71395)
        self.assertEqual(items[0].account, "Conta Exemplo PJ.")
        self.assertFalse(occurs(data[0], "2027-05"))

    def test_actual_and_third_party(self):
        items, issues = interpret("Gastei R$ 35 no Uber hoje\nMeu pai pagou R$ 150 de academia ontem", self.today)
        self.assertFalse(issues, issues)
        self.assertEqual(items[0].frequency, "actual")
        self.assertEqual(items[0].day, "2026-11-25")
        self.assertEqual(items[1].payer, "third")
        self.assertEqual(items[1].day, "2026-11-24")
        self.assertEqual(plan_totals([asdict(i) for i in items], "2026-11")["third_actual"], 15000)

    def test_multiple_months(self):
        items, issues = interpret("Dívida: R$ 250,00 em novembro e R$ 250,00 em dezembro.", self.today)
        self.assertFalse(issues, issues)
        self.assertEqual([i.month for i in items], ["2026-11", "2026-12"])

    def test_ambiguous_values(self):
        for line in ["R$ 400 previstos para fim de semana", "Comprei R$ 900 em 3x", "Gastei R$ 20 e R$ 30 hoje", "Gastei R$ 35 em 31/02/2026", "Gastei R$ -10 hoje", "Meu pai não pagou R$ 50 ontem", "Meu pai paga academia R$ 150"]:
            items, issues = interpret(line, self.today)
            self.assertFalse(items, line)
            self.assertTrue(issues, line)

    def test_duplicate_key(self):
        a, _ = interpret("Academia: R$ 150/mês, paga pelo meu pai", self.today)
        b, _ = interpret("academia: R$ 150,00 por mês, paga pelo meu pai", self.today)
        self.assertEqual(item_key(asdict(a[0])), item_key(asdict(b[0])))


if __name__ == "__main__":
    unittest.main()
