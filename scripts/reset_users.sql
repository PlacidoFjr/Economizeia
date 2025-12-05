-- Script para apagar todos os usuários e dados relacionados
-- ⚠️ ATENÇÃO: Isso apaga TODOS os dados do sistema!

-- 1. Apagar dados relacionados primeiro (devido a foreign keys)
DELETE FROM audit_logs;
DELETE FROM notifications;
DELETE FROM payments;
DELETE FROM bills;

-- 2. Apagar todos os usuários
DELETE FROM users;

-- 3. Verificar se foi apagado
SELECT COUNT(*) as total_usuarios FROM users;
SELECT COUNT(*) as total_bills FROM bills;
SELECT COUNT(*) as total_payments FROM payments;

