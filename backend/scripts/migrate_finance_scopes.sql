-- EconomizeIA: financeiro pessoal-PJ
-- Run on staging first; back up production before deployment.
BEGIN;
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS scope VARCHAR(20) NOT NULL DEFAULT 'personal';
ALTER TABLE bills ADD COLUMN IF NOT EXISTS scope VARCHAR(20) NOT NULL DEFAULT 'personal';
ALTER TABLE bills ADD COLUMN IF NOT EXISTS paid_by VARCHAR(20) NOT NULL DEFAULT 'self';
ALTER TABLE bills ADD COLUMN IF NOT EXISTS account_id UUID REFERENCES accounts(id);
ALTER TABLE savings_goals ADD COLUMN IF NOT EXISTS scope VARCHAR(20) NOT NULL DEFAULT 'personal';
ALTER TABLE investments ADD COLUMN IF NOT EXISTS scope VARCHAR(20) NOT NULL DEFAULT 'personal';
CREATE TABLE IF NOT EXISTS monthly_budgets (
  id UUID PRIMARY KEY, user_id UUID NOT NULL REFERENCES users(id),
  scope VARCHAR(20) NOT NULL DEFAULT 'personal', category VARCHAR(50) NOT NULL,
  month DATE NOT NULL, amount DOUBLE PRECISION NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_monthly_budgets_user_id ON monthly_budgets(user_id);
CREATE TABLE IF NOT EXISTS planned_entries (
  id UUID PRIMARY KEY, user_id UUID NOT NULL REFERENCES users(id),
  scope VARCHAR(20) NOT NULL DEFAULT 'personal', title VARCHAR(255) NOT NULL,
  type VARCHAR(20) NOT NULL, amount DOUBLE PRECISION NOT NULL,
  planned_date DATE NOT NULL, category VARCHAR(50),
  paid_by VARCHAR(20) NOT NULL DEFAULT 'self', status VARCHAR(20) NOT NULL DEFAULT 'planned',
  realized_bill_id UUID REFERENCES bills(id), created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_planned_entries_user_id ON planned_entries(user_id);
CREATE INDEX IF NOT EXISTS ix_planned_entries_planned_date ON planned_entries(planned_date);
CREATE TABLE IF NOT EXISTS account_transfers (
  id UUID PRIMARY KEY, user_id UUID NOT NULL REFERENCES users(id),
  from_account_id UUID NOT NULL REFERENCES accounts(id),
  to_account_id UUID NOT NULL REFERENCES accounts(id),
  amount DOUBLE PRECISION NOT NULL, transferred_on DATE NOT NULL,
  notes VARCHAR(255), created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_account_transfers_user_id ON account_transfers(user_id);
COMMIT;
