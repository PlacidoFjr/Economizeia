// Traduções para status e textos da aplicação

export const translateStatus = (status: string): string => {
  const translations: Record<string, string> = {
    'pending': 'Pendente',
    'confirmed': 'Confirmado',
    'scheduled': 'Agendado',
    'paid': 'Pago',
    'overdue': 'Vencido',
    'cancelled': 'Cancelado',
    'executed': 'Executado',
    'failed': 'Falhou',
  }
  return translations[status] || status
}

export const translatePaymentMethod = (method: string): string => {
  const translations: Record<string, string> = {
    'PIX': 'PIX',
    'BOLETO': 'Boleto',
    'DEBIT': 'Débito Automático',
    'CREDIT': 'Cartão de Crédito',
    'TRANSFER': 'Transferência',
  }
  return translations[method] || method
}

export const translateCategory = (category: string): string => {
  const translations: Record<string, string> = {
    'alimentacao': 'Alimentação',
    'moradia': 'Moradia',
    'servicos': 'Serviços',
    'transporte': 'Transporte',
    'saude': 'Saúde',
    'investimentos': 'Investimentos',
    'outras': 'Outras',
  }
  return translations[category] || category
}

