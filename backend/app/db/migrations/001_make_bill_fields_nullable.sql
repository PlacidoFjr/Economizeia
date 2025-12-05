-- Migration: Tornar campos amount e due_date nullable na tabela bills
-- Isso permite criar boletos antes do OCR extrair esses valores

-- Alterar coluna amount para permitir NULL
ALTER TABLE bills ALTER COLUMN amount DROP NOT NULL;

-- Alterar coluna due_date para permitir NULL
ALTER TABLE bills ALTER COLUMN due_date DROP NOT NULL;

-- Comentários para documentação
COMMENT ON COLUMN bills.amount IS 'Valor do boleto. Pode ser NULL até o OCR extrair o valor.';
COMMENT ON COLUMN bills.due_date IS 'Data de vencimento. Pode ser NULL até o OCR extrair a data.';

