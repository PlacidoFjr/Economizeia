-- EconomizeIA Database Schema
-- PostgreSQL 15+

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    notif_prefs JSONB DEFAULT '{"email_enabled": true, "sms_enabled": false, "push_enabled": true, "reminder_days": [7, 3, 1]}'::jsonb
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active);

-- Accounts table
CREATE TABLE IF NOT EXISTS accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    estimated_balance DECIMAL(12,2) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_accounts_user_id ON accounts(user_id);

-- Bills table
CREATE TABLE IF NOT EXISTS bills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    issuer VARCHAR(255),
    amount DECIMAL(12,2),  -- Nullable para permitir upload antes do OCR
    currency VARCHAR(3) DEFAULT 'BRL',
    due_date DATE,  -- Nullable para permitir upload antes do OCR
    barcode VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pending',
    type VARCHAR(20) DEFAULT 'expense',
    is_bill BOOLEAN DEFAULT TRUE,
    confidence DECIMAL(3,2) DEFAULT 0.0,
    category VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_bills_user_id ON bills(user_id);
CREATE INDEX idx_bills_due_date ON bills(due_date);
CREATE INDEX idx_bills_status ON bills(status);
CREATE INDEX idx_bills_type ON bills(type);
CREATE INDEX idx_bills_is_bill ON bills(is_bill);
CREATE INDEX idx_bills_confidence ON bills(confidence) WHERE confidence < 0.9;

-- Bill documents table
CREATE TABLE IF NOT EXISTS bill_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bill_id UUID NOT NULL REFERENCES bills(id) ON DELETE CASCADE,
    s3_path VARCHAR(500) NOT NULL,
    ocr_text TEXT,
    ocr_confidence DECIMAL(3,2) DEFAULT 0.0,
    extracted_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_bill_documents_bill_id ON bill_documents(bill_id);

-- Payments table
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bill_id UUID NOT NULL REFERENCES bills(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scheduled_date DATE NOT NULL,
    executed_date DATE,
    method VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'scheduled',
    comprovante_path VARCHAR(500),
    notify_before_days JSONB DEFAULT '[7, 3, 1]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_payments_bill_id ON payments(bill_id);
CREATE INDEX idx_payments_user_id ON payments(user_id);
CREATE INDEX idx_payments_scheduled_date ON payments(scheduled_date);
CREATE INDEX idx_payments_status ON payments(status);

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    channel VARCHAR(20) NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE,
    payload JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);

-- Audit logs table (immutable)
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    user_id UUID REFERENCES users(id),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    details JSONB,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500)
);

CREATE INDEX idx_audit_logs_entity ON audit_logs(entity);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);

-- Function to prevent updates/deletes on audit_logs
CREATE OR REPLACE FUNCTION prevent_audit_log_modification()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'Audit logs are immutable';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_logs_immutable
    BEFORE UPDATE OR DELETE ON audit_logs
    FOR EACH ROW
    EXECUTE FUNCTION prevent_audit_log_modification();

-- Savings Goals table (Metas de Economia)
CREATE TABLE IF NOT EXISTS savings_goals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    target_amount DECIMAL(12,2) NOT NULL,
    current_amount DECIMAL(12,2) DEFAULT 0.0,
    deadline DATE NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'active',
    notify_days_before JSONB DEFAULT '[30, 15, 7, 3, 1]'::jsonb,
    last_notification_sent DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_savings_goals_user_id ON savings_goals(user_id);
CREATE INDEX idx_savings_goals_status ON savings_goals(status);
CREATE INDEX idx_savings_goals_deadline ON savings_goals(deadline);

-- Investments table (Investimentos)
CREATE TABLE IF NOT EXISTS investments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    amount_invested DECIMAL(12,2) NOT NULL,
    current_value DECIMAL(12,2),
    purchase_date DATE NOT NULL,
    sell_date DATE,
    institution VARCHAR(255),
    ticker VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_investments_user_id ON investments(user_id);
CREATE INDEX idx_investments_type ON investments(type);
CREATE INDEX idx_investments_purchase_date ON investments(purchase_date);

