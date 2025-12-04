# Política de Segurança - FinGuia

## Visão Geral

Este documento descreve as práticas de segurança implementadas no FinGuia para garantir a proteção dos dados dos usuários e conformidade com a LGPD.

## Autenticação e Autorização

### JWT Tokens
- **Access Token**: Expira em 30 minutos (configurável)
- **Refresh Token**: Expira em 7 dias (configurável)
- Tokens são assinados com algoritmo HS256
- Refresh tokens são armazenados de forma segura

### Hashing de Senhas
- **Algoritmo**: Argon2id
- Senhas nunca são armazenadas em texto plano
- Verificação de senha com proteção contra timing attacks

### Autorização
- Todos os endpoints protegidos requerem autenticação
- Acesso baseado em `user_id` - usuários só acessam seus próprios dados
- Validação de permissões em todas as operações sensíveis

## Criptografia

### Em Trânsito
- **TLS obrigatório** em produção
- Todas as comunicações HTTPS
- Certificados SSL válidos

### Em Repouso
- **AES-256** para dados sensíveis
- Chaves de criptografia gerenciadas de forma segura
- Dados sensíveis (CPF/CNPJ) mascarados em previews

## Proteção de Dados Pessoais (LGPD)

### Mascaramento
- CPFs e CNPJs são mascarados em visualizações
- Dados completos apenas para operações autorizadas
- Logs não contêm dados sensíveis completos

### Retenção de Dados
- Período de retenção configurável (padrão: 365 dias)
- Endpoint para exclusão de dados do usuário
- Portabilidade de dados disponível

### Consentimento
- Consentimento explícito ao fazer upload de arquivos
- Política de privacidade clara
- Opções de opt-out para notificações

## Auditoria

### Logs Imutáveis
- Todos os logs de auditoria são imutáveis
- Trigger no banco de dados previne modificação
- Registro de todas as ações sensíveis:
  - Criação/edição de boletos
  - Agendamento de pagamentos
  - Marcação como pago
  - Confirmação de dados
  - Login/logout

### Informações Registradas
- Timestamp
- User ID
- Ação realizada
- IP address
- User agent
- Detalhes da operação (JSON)

## Armazenamento

### MinIO/S3
- Buckets com políticas de acesso restritas
- URLs pré-assinadas com expiração
- Backup automático configurado

### Banco de Dados
- PostgreSQL com conexões SSL
- Backups regulares
- Isolamento de dados por usuário

## Notificações

### Canais Seguros
- Email via SMTP/TLS
- SMS via provider confiável
- Push notifications com tokens seguros

### Dados em Notificações
- Não incluem dados sensíveis completos
- Links seguros com tokens temporários
- Opção de desabilitar notificações

## Vulnerabilidades Conhecidas

### OCR e Processamento
- Arquivos enviados são processados em ambiente isolado
- Validação de tipos de arquivo
- Limite de tamanho de arquivo (10MB)

### API
- Rate limiting implementado
- Validação de entrada em todos os endpoints
- Proteção contra SQL injection (ORM)
- Proteção contra XSS (sanitização)

## Recomendações de Produção

1. **Variáveis de Ambiente**
   - Nunca commitar `.env` no repositório
   - Usar gerenciador de secrets (AWS Secrets Manager, etc)
   - Rotacionar chaves regularmente

2. **Monitoramento**
   - Logs centralizados
   - Alertas de segurança
   - Monitoramento de tentativas de acesso

3. **Backup**
   - Backups diários
   - Teste de restauração regular
   - Backup off-site

4. **Atualizações**
   - Manter dependências atualizadas
   - Aplicar patches de segurança
   - Revisar vulnerabilidades regularmente

## Contato

Para reportar vulnerabilidades de segurança, entre em contato com a equipe de segurança.

