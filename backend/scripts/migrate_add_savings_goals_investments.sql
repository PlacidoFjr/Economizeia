-- Migração: Adicionar tabelas de Metas de Economia e Investimentos
-- Execute este script no seu banco de dados PostgreSQL

-- Verificar se as tabelas já existem antes de criar
DO $$
BEGIN
    -- Savings Goals table (Metas de Economia)
    IF NOT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'savings_goals') THEN
        CREATE TABLE savings_goals (
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

        RAISE NOTICE 'Tabela savings_goals criada com sucesso!';
    ELSE
        RAISE NOTICE 'Tabela savings_goals já existe.';
    END IF;

    -- Investments table (Investimentos)
    IF NOT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'investments') THEN
        CREATE TABLE investments (
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

        RAISE NOTICE 'Tabela investments criada com sucesso!';
    ELSE
        RAISE NOTICE 'Tabela investments já existe.';
    END IF;

    -- Adicionar novos tipos de notificação se não existirem
    -- (Nota: Se você usar ENUMs, pode precisar de ALTER TYPE)
    RAISE NOTICE 'Migração concluída!';
END $$;

