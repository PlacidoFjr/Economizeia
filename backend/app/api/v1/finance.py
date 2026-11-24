"""Planejamento financeiro pessoal/PJ. Valores planejados nunca entram no saldo realizado."""
from datetime import date
from typing import Literal, Optional
from uuid import UUID, uuid4

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import (
    Account, AccountTransfer, Bill, BillStatus, BillType,
    MonthlyBudget, PlannedEntry, User,
)

router = APIRouter()
Scope = Literal["personal", "business"]
Payer = Literal["self", "family", "business", "other"]
MovementType = Literal["income", "expense"]
REALIZED = {BillStatus.PAID, BillStatus.CONFIRMED}


class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    type: Literal["checking", "savings", "credit", "business"] = "checking"
    scope: Scope = "personal"
    opening_balance: float = Field(default=0.0, ge=-1_000_000_000, le=1_000_000_000)


class BudgetInput(BaseModel):
    scope: Scope = "personal"
    month: date
    category: str = Field(min_length=1, max_length=50)
    amount: float = Field(ge=0, le=1_000_000_000)


class RecurringInput(BaseModel):
    scope: Scope = "personal"
    title: str = Field(min_length=1, max_length=255)
    type: MovementType
    amount: float = Field(gt=0, le=1_000_000_000)
    first_due: date
    months: int = Field(default=1, ge=1, le=24)
    category: Optional[str] = Field(default=None, max_length=50)
    paid_by: Payer = "self"


class RealizeInput(BaseModel):
    account_id: Optional[UUID] = None


class TransferInput(BaseModel):
    from_account_id: UUID
    to_account_id: UUID
    amount: float = Field(gt=0, le=1_000_000_000)
    transferred_on: date
    notes: Optional[str] = Field(default=None, max_length=255)


def first_day(value: date) -> date:
    return value.replace(day=1)


def month_bounds(value: date):
    beginning = first_day(value)
    return beginning, beginning + relativedelta(months=1)


def is_own_movement(bill: Bill) -> bool:
    return bill.paid_by in ("self", "business")


def is_realized(bill: Bill) -> bool:
    return bill.status in REALIZED and bill.amount is not None


def bill_amounts(bills):
    """Dinheiro movimentado x custo de vida pago por terceiros, sem dupla contagem."""
    income = expense = supported = 0.0
    for bill in bills:
        if not is_realized(bill):
            continue
        if bill.type == BillType.INCOME:
            if is_own_movement(bill):
                income += bill.amount
        elif is_own_movement(bill):
            expense += bill.amount
        else:
            supported += bill.amount
    return {
        "income": round(income, 2),
        "expenses": round(expense, 2),
        "third_party_expenses": round(supported, 2),
        "balance": round(income - expense, 2),
    }


def scoped_bills(db, user_id, scope, start=None, end=None):
    q = db.query(Bill).filter(Bill.user_id == user_id, Bill.scope == scope)
    if start:
        q = q.filter(Bill.due_date >= start)
    if end:
        q = q.filter(Bill.due_date < end)
    return q.all()


def serialize_plan(plan):
    return {
        "id": str(plan.id), "scope": plan.scope, "title": plan.title,
        "type": plan.type, "amount": plan.amount,
        "planned_date": plan.planned_date.isoformat(),
        "category": plan.category, "paid_by": plan.paid_by, "status": plan.status,
        "realized_bill_id": str(plan.realized_bill_id) if plan.realized_bill_id else None,
    }


@router.get("/overview")
def overview(
    scope: Scope = "personal",
    month: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    start, end = month_bounds(month or date.today())
    bills = scoped_bills(db, current_user.id, scope, start, end)
    totals = bill_amounts(bills)
    plans = db.query(PlannedEntry).filter(
        PlannedEntry.user_id == current_user.id, PlannedEntry.scope == scope,
        PlannedEntry.planned_date >= start, PlannedEntry.planned_date < end,
        PlannedEntry.status == "planned",
    ).all()
    budgets = db.query(MonthlyBudget).filter(
        MonthlyBudget.user_id == current_user.id,
        MonthlyBudget.scope == scope,
        MonthlyBudget.month == start,
    ).all()
    spending_by_category = {}
    for bill in bills:
        if is_realized(bill) and bill.type == BillType.EXPENSE and is_own_movement(bill):
            key = bill.category or "outras"
            spending_by_category[key] = round(spending_by_category.get(key, 0.0) + bill.amount, 2)
    return {
        "scope": scope, "month": start.isoformat(), **totals,
        "planned_income": round(sum(p.amount for p in plans if p.type == "income"), 2),
        "planned_expenses": round(sum(p.amount for p in plans if p.type == "expense" and p.paid_by in ("self", "business")), 2),
        "planned_third_party": round(sum(p.amount for p in plans if p.type == "expense" and p.paid_by not in ("self", "business")), 2),
        "budgets": [
            {"category": b.category, "limit": b.amount,
             "spent": spending_by_category.get(b.category, 0.0),
             "remaining": round(b.amount - spending_by_category.get(b.category, 0.0), 2)}
            for b in budgets
        ],
    }


@router.get("/budgets")
def list_budgets(
    scope: Scope = "personal",
    month: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    start = first_day(month or date.today())
    budgets = db.query(MonthlyBudget).filter(
        MonthlyBudget.user_id == current_user.id,
        MonthlyBudget.scope == scope,
        MonthlyBudget.month == start,
    ).all()
    return [
        {"id": str(b.id), "scope": b.scope, "month": b.month.isoformat(),
         "category": b.category, "amount": b.amount}
        for b in budgets
    ]


@router.put("/budgets")
def upsert_budget(
    data: BudgetInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    month = first_day(data.month)
    item = db.query(MonthlyBudget).filter(
        MonthlyBudget.user_id == current_user.id,
        MonthlyBudget.scope == data.scope,
        MonthlyBudget.month == month,
        MonthlyBudget.category == data.category,
    ).first()
    if item is None:
        item = MonthlyBudget(user_id=current_user.id, scope=data.scope, month=month, category=data.category)
        db.add(item)
    item.amount = data.amount
    db.commit()
    return {"id": str(item.id), "category": item.category, "month": month.isoformat(), "amount": item.amount}


@router.get("/accounts")
def list_accounts(
    scope: Optional[Scope] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Account).filter(Account.user_id == current_user.id)
    if scope:
        q = q.filter(Account.scope == scope)
    accounts = q.order_by(Account.created_at).all()
    bills = db.query(Bill).filter(Bill.user_id == current_user.id, Bill.account_id.isnot(None)).all()
    transfers = db.query(AccountTransfer).filter(AccountTransfer.user_id == current_user.id).all()
    output = []
    for account in accounts:
        total = float(account.estimated_balance or 0)
        for bill in bills:
            if bill.account_id == account.id and is_realized(bill) and is_own_movement(bill):
                total += bill.amount if bill.type == BillType.INCOME else -bill.amount
        for transfer in transfers:
            if transfer.from_account_id == account.id:
                total -= transfer.amount
            if transfer.to_account_id == account.id:
                total += transfer.amount
        output.append({
            "id": str(account.id), "name": account.name,
            "type": account.type, "scope": account.scope,
            "opening_balance": account.estimated_balance or 0,
            "calculated_balance": round(total, 2),
        })
    return output


@router.post("/accounts", status_code=201)
def create_account(
    data: AccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = Account(
        id=uuid4(), user_id=current_user.id, name=data.name.strip(),
        type=data.type, scope=data.scope, estimated_balance=data.opening_balance,
    )
    db.add(account)
    db.commit()
    return {"id": str(account.id), "name": account.name, "scope": account.scope}


@router.post("/transfers", status_code=201)
def transfer(
    data: TransferInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.from_account_id == data.to_account_id:
        raise HTTPException(status_code=400, detail="Contas de origem e destino devem ser diferentes")
    accounts = db.query(Account).filter(
        Account.user_id == current_user.id,
        Account.id.in_([data.from_account_id, data.to_account_id]),
    ).all()
    if len(accounts) != 2:
        raise HTTPException(status_code=404, detail="Uma das contas nao pertence ao usuario")
    item = AccountTransfer(
        id=uuid4(), user_id=current_user.id,
        from_account_id=data.from_account_id, to_account_id=data.to_account_id,
        amount=data.amount, transferred_on=data.transferred_on, notes=data.notes,
    )
    db.add(item)
    db.commit()
    return {"id": str(item.id), "amount": item.amount, "transferred_on": item.transferred_on.isoformat()}


@router.get("/transfers")
def list_transfers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.query(AccountTransfer).filter(
        AccountTransfer.user_id == current_user.id
    ).order_by(AccountTransfer.transferred_on.desc()).all()
    return [
        {"id": str(t.id), "from_account_id": str(t.from_account_id),
         "to_account_id": str(t.to_account_id), "amount": t.amount,
         "transferred_on": t.transferred_on.isoformat(), "notes": t.notes}
        for t in rows
    ]


@router.post("/plans/recurring", status_code=201)
def create_recurring_plan(
    data: RecurringInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Cria previsoes, nao receitas realizadas. Nenhum valor entra no saldo.
    first = data.first_due
    if data.scope == 'business' and data.paid_by in ('family', 'other'):
        raise HTTPException(status_code=400, detail='Previsao PJ nao pode ser paga por terceiros')
    items = []
    for index in range(data.months):
        item = PlannedEntry(
            id=uuid4(), user_id=current_user.id, scope=data.scope,
            title=data.title.strip(), type=data.type, amount=data.amount,
            planned_date=first + relativedelta(months=index),
            category=data.category,
            paid_by=data.paid_by if data.scope == "personal" else "business",
            status="planned",
        )
        db.add(item)
        items.append(item)
    db.commit()
    return [serialize_plan(item) for item in items]


@router.get("/plans")
def list_plans(
    scope: Scope = "personal",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plans = db.query(PlannedEntry).filter(
        PlannedEntry.user_id == current_user.id,
        PlannedEntry.scope == scope,
    ).order_by(PlannedEntry.planned_date).all()
    return [serialize_plan(item) for item in plans]


@router.post("/plans/{plan_id}/realize")
def realize_plan(
    plan_id: UUID,
    data: RealizeInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Row lock evita duas realizacoes simultaneas do mesmo planejamento.
    plan = db.query(PlannedEntry).filter(
        PlannedEntry.id == plan_id, PlannedEntry.user_id == current_user.id
    ).with_for_update().first()
    if not plan:
        raise HTTPException(status_code=404, detail="Previsao nao encontrada")
    if plan.status != "planned":
        raise HTTPException(status_code=409, detail="Previsao ja realizada ou cancelada")
    if data.account_id:
        account = db.query(Account).filter(
            Account.id == data.account_id,
            Account.user_id == current_user.id,
            Account.scope == plan.scope,
        ).first()
        if not account:
            raise HTTPException(status_code=400, detail="Conta invalida para este contexto")
        if plan.paid_by not in ("self", "business"):
            raise HTTPException(status_code=400, detail="Despesas pagas por terceiros nao movimentam sua conta")
    if plan.scope == 'business' and plan.paid_by != 'business':
        raise HTTPException(status_code=400, detail='Previsao PJ com pagador invalido')
    bill = Bill(
        id=uuid4(), user_id=current_user.id, issuer=plan.title,
        amount=plan.amount, currency="BRL", due_date=plan.planned_date,
        status=BillStatus.PAID, type=BillType(plan.type), is_bill=False,
        confidence=1.0, category=plan.category,
        scope=plan.scope, paid_by=plan.paid_by, account_id=data.account_id,
    )
    db.add(bill)
    plan.status = "realized"
    plan.realized_bill_id = bill.id
    db.commit()
    return {"id": str(plan.id), "realized_bill_id": str(bill.id), "status": "realized"}


@router.delete("/plans/{plan_id}", status_code=204)
def cancel_plan(
    plan_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = db.query(PlannedEntry).filter(
        PlannedEntry.id == plan_id, PlannedEntry.user_id == current_user.id
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Previsao nao encontrada")
    if plan.status != "planned":
        raise HTTPException(status_code=409, detail="Apenas previsoes pendentes podem ser canceladas")
    plan.status = "cancelled"
    db.commit()


@router.get("/projection")
def projection(
    scope: Scope = "personal",
    start_month: Optional[date] = None,
    months: int = 6,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not 1 <= months <= 24:
        raise HTTPException(status_code=400, detail="Periodo deve ter entre 1 e 24 meses")
    start = first_day(start_month or date.today())
    finish = start + relativedelta(months=months)
    plans = db.query(PlannedEntry).filter(
        PlannedEntry.user_id == current_user.id, PlannedEntry.scope == scope,
        PlannedEntry.planned_date >= start, PlannedEntry.planned_date < finish,
        PlannedEntry.status == "planned",
    ).all()
    bills = scoped_bills(db, current_user.id, scope, start, finish)
    rows = []
    for index in range(months):
        month = start + relativedelta(months=index)
        end = month + relativedelta(months=1)
        planned = [p for p in plans if month <= p.planned_date < end]
        actual = bill_amounts([b for b in bills if b.due_date and month <= b.due_date < end])
        expected_income = sum(p.amount for p in planned if p.type == "income" and p.paid_by in ("self", "business"))
        expected_expenses = sum(p.amount for p in planned if p.type == "expense" and p.paid_by in ("self", "business"))
        rows.append({
            "month": month.isoformat(),
            **actual,
            "future_income": round(expected_income, 2),
            "future_expenses": round(expected_expenses, 2),
            "projected_net": round(actual["balance"] + expected_income - expected_expenses, 2),
        })
    return rows
