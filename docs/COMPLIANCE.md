# Compliance LGPD - FinGuia

## Conformidade com a Lei Geral de Proteção de Dados

Este documento descreve como o FinGuia atende aos requisitos da LGPD (Lei 13.709/2018).

## Princípios da LGPD

### 1. Finalidade
- **Objetivo**: Organização financeira pessoal do usuário
- Dados coletados apenas para fins específicos e legítimos
- Sem uso de dados para outros fins sem consentimento

### 2. Adequação
- Dados coletados são adequados ao propósito
- Apenas dados necessários são solicitados
- Dados sensíveis (CPF/CNPJ) apenas quando necessário

### 3. Necessidade
- Coleta mínima de dados
- Dados não são mantidos além do necessário
- Retenção configurável pelo usuário

### 4. Transparência
- Política de privacidade clara
- Informações sobre uso de dados
- Consentimento explícito

### 5. Segurança
- Medidas técnicas e administrativas
- Criptografia em trânsito e repouso
- Acesso restrito aos dados

### 6. Prevenção
- Medidas preventivas de segurança
- Monitoramento e detecção de anomalias
- Plano de resposta a incidentes

### 7. Não Discriminação
- Dados não utilizados para discriminação
- Tratamento justo e equitativo

### 8. Responsabilização
- Responsável pelo tratamento identificado
- Demonstração de conformidade
- Auditoria e logs

## Direitos do Titular

### 1. Confirmação de Existência
- Endpoint: `GET /api/v1/user/data`
- Usuário pode verificar quais dados estão armazenados

### 2. Acesso aos Dados
- Endpoint: `GET /api/v1/user/export`
- Exportação completa dos dados em formato JSON
- Inclui todos os boletos, pagamentos e configurações

### 3. Correção de Dados
- Endpoint: `POST /api/v1/bills/{id}/confirm`
- Usuário pode corrigir dados extraídos incorretamente
- Edição de campos de boletos

### 4. Anonimização, Bloqueio ou Eliminação
- Endpoint: `DELETE /api/v1/user/data`
- Exclusão completa dos dados do usuário
- Anonimização de dados históricos (se aplicável)

### 5. Portabilidade
- Endpoint: `GET /api/v1/user/export`
- Dados exportados em formato estruturado
- Facilita migração para outros sistemas

### 6. Eliminação de Dados
- Endpoint: `DELETE /api/v1/user/data`
- Exclusão permanente após período de retenção
- Confirmação antes da exclusão

### 7. Informação sobre Compartilhamento
- Política de privacidade detalha compartilhamento
- Consentimento para compartilhamento com terceiros
- Lista de provedores de serviços

### 8. Informação sobre Possibilidade de Não Consentir
- Opções claras de consentimento
- Possibilidade de recusar tratamento de dados
- Consequências da recusa explicadas

### 9. Revogação do Consentimento
- Endpoint: `POST /api/v1/user/consent/revoke`
- Revogação de consentimento a qualquer momento
- Exclusão de dados após revogação (se aplicável)

## Base Legal

### Consentimento
- Consentimento explícito ao criar conta
- Consentimento para upload de documentos
- Consentimento para notificações

### Execução de Contrato
- Processamento necessário para prestação do serviço
- Gestão de boletos e pagamentos

### Legítimo Interesse
- Detecção de fraudes
- Melhoria do serviço
- Análise de uso (anônima)

## Medidas de Segurança

### Técnicas
- Criptografia AES-256
- TLS para comunicações
- Hashing de senhas (Argon2id)
- Logs de auditoria imutáveis
- Isolamento de dados por usuário

### Administrativas
- Política de acesso restrito
- Treinamento da equipe
- Procedimentos de resposta a incidentes
- Revisão regular de segurança

## Retenção de Dados

### Período Padrão
- **Dados ativos**: Enquanto a conta estiver ativa
- **Dados inativos**: 365 dias após última atividade
- **Logs de auditoria**: 7 anos (requisito legal)

### Exclusão
- Exclusão automática após período de retenção
- Exclusão manual a qualquer momento
- Confirmação antes da exclusão permanente

## Compartilhamento com Terceiros

### Provedores de Serviço
- **Ollama**: Processamento de IA (dados anonimizados)
- **MinIO/S3**: Armazenamento de arquivos
- **SMTP Provider**: Envio de emails
- **SMS Provider**: Envio de SMS

### Contratos
- Todos os provedores com cláusulas de proteção de dados
- Transferência internacional apenas com garantias adequadas
- Auditoria regular de provedores

## Incidentes de Segurança

### Procedimento
1. Detecção do incidente
2. Isolamento imediato
3. Análise do impacto
4. Notificação à ANPD (se necessário)
5. Notificação aos titulares afetados
6. Correção e prevenção

### Notificação
- Notificação à ANPD em até 72 horas
- Notificação aos titulares se houver risco
- Comunicação clara e transparente

## Contato DPO

Para questões sobre proteção de dados:
- Email: dpo@finguia.com
- Formulário: /contact/dpo

## Atualizações

Esta política é revisada regularmente e atualizada conforme necessário. Última atualização: 2025-01-XX

