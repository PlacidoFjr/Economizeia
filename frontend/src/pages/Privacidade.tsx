import { Link } from 'react-router-dom'
import { Shield, ArrowLeft } from 'lucide-react'

export default function Privacidade() {
  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-8 md:p-12">
          {/* Header */}
          <div className="mb-8">
            <Link
              to="/register"
              className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-6 transition-colors"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Voltar para Registro
            </Link>
            <div className="flex items-center mb-4">
              <div className="bg-gray-100 p-3 rounded-lg mr-4">
                <Shield className="w-8 h-8 text-gray-700" />
              </div>
              <div>
                <h1 className="text-4xl font-bold text-gray-900">Política de Privacidade</h1>
                <p className="text-gray-600 mt-1">Última atualização: 04 de dezembro de 2024</p>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="prose prose-lg max-w-none">
            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">1. Introdução</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                O EconomizeIA está comprometido em proteger sua privacidade e seus dados pessoais. Esta Política de Privacidade 
                descreve como coletamos, usamos, armazenamos e protegemos suas informações pessoais em conformidade com a 
                Lei Geral de Proteção de Dados (LGPD - Lei nº 13.709/2018).
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">2. Dados Coletados</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                Coletamos os seguintes tipos de dados pessoais:
              </p>
              
              <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">2.1. Dados de Cadastro</h3>
              <ul className="list-disc list-inside text-gray-700 space-y-2 mb-4 ml-4">
                <li>Nome completo</li>
                <li>Endereço de email</li>
                <li>Senha (criptografada)</li>
                <li>Número de telefone (opcional)</li>
              </ul>

              <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">2.2. Dados Financeiros</h3>
              <ul className="list-disc list-inside text-gray-700 space-y-2 mb-4 ml-4">
                <li>Boletos e faturas enviados</li>
                <li>Valores, datas de vencimento e emissores</li>
                <li>Códigos de barras</li>
                <li>Categorias de despesas</li>
                <li>Histórico de pagamentos</li>
                <li>Receitas cadastradas</li>
              </ul>

              <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">2.3. Dados de Uso</h3>
              <ul className="list-disc list-inside text-gray-700 space-y-2 mb-4 ml-4">
                <li>Logs de acesso e atividades</li>
                <li>Preferências de notificação</li>
                <li>Histórico de conversas com o assistente virtual</li>
                <li>Configurações do sistema</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">3. Como Utilizamos Seus Dados</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                Utilizamos seus dados pessoais para:
              </p>
              <ul className="list-disc list-inside text-gray-700 space-y-2 mb-4 ml-4">
                <li>Fornecer e melhorar nossos serviços de gestão financeira</li>
                <li>Processar e extrair informações de boletos através de OCR e IA</li>
                <li>Enviar notificações e lembretes de pagamento</li>
                <li>Gerar relatórios e análises financeiras personalizadas</li>
                <li>Garantir a segurança e prevenir fraudes</li>
                <li>Cumprir obrigações legais e regulatórias</li>
                <li>Comunicar atualizações e melhorias do serviço</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">4. Base Legal para Tratamento</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                O tratamento de seus dados pessoais é baseado em:
              </p>
              <ul className="list-disc list-inside text-gray-700 space-y-2 mb-4 ml-4">
                <li><strong>Consentimento:</strong> Você consente explicitamente ao criar uma conta e usar nossos serviços</li>
                <li><strong>Execução de contrato:</strong> Necessário para fornecer os serviços solicitados</li>
                <li><strong>Obrigação legal:</strong> Cumprimento de obrigações legais e regulatórias</li>
                <li><strong>Legítimo interesse:</strong> Melhorar nossos serviços e garantir segurança</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">5. Compartilhamento de Dados</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                Não vendemos, alugamos ou compartilhamos seus dados pessoais com terceiros, exceto nas seguintes situações:
              </p>
              <ul className="list-disc list-inside text-gray-700 space-y-2 mb-4 ml-4">
                <li><strong>Prestadores de serviço:</strong> Empresas que nos auxiliam na operação (hospedagem, email, etc.), 
                sempre sob contratos de confidencialidade</li>
                <li><strong>Obrigação legal:</strong> Quando exigido por lei, ordem judicial ou autoridade competente</li>
                <li><strong>Com seu consentimento:</strong> Quando você autorizar explicitamente</li>
                <li><strong>Proteção de direitos:</strong> Para proteger nossos direitos, propriedade ou segurança</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">6. Segurança dos Dados</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                Implementamos medidas técnicas e organizacionais para proteger seus dados:
              </p>
              <ul className="list-disc list-inside text-gray-700 space-y-2 mb-4 ml-4">
                <li><strong>Criptografia:</strong> Dados sensíveis são criptografados em trânsito (TLS) e em repouso (AES-256)</li>
                <li><strong>Autenticação:</strong> Senhas são armazenadas usando Argon2id (hashing seguro)</li>
                <li><strong>Acesso restrito:</strong> Apenas pessoal autorizado tem acesso aos dados</li>
                <li><strong>Mascaramento:</strong> Dados sensíveis como CPF/CNPJ são mascarados em logs</li>
                <li><strong>Monitoramento:</strong> Sistemas de monitoramento e detecção de anomalias</li>
                <li><strong>Backups seguros:</strong> Backups regulares e criptografados</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">7. Retenção de Dados</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                Mantemos seus dados pessoais pelo tempo necessário para:
              </p>
              <ul className="list-disc list-inside text-gray-700 space-y-2 mb-4 ml-4">
                <li>Fornecer os serviços solicitados</li>
                <li>Cumprir obrigações legais e regulatórias</li>
                <li>Resolver disputas e fazer cumprir nossos acordos</li>
                <li>Após o encerramento da conta, os dados podem ser mantidos por até 5 anos para fins legais</li>
              </ul>
              <p className="text-gray-700 leading-relaxed mb-4 mt-4">
                Você pode solicitar a exclusão de seus dados a qualquer momento, sujeito a obrigações legais de retenção.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">8. Seus Direitos (LGPD)</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                De acordo com a LGPD, você tem os seguintes direitos:
              </p>
              <ul className="list-disc list-inside text-gray-700 space-y-2 mb-4 ml-4">
                <li><strong>Confirmação e acesso:</strong> Saber se tratamos seus dados e acessá-los</li>
                <li><strong>Correção:</strong> Solicitar correção de dados incompletos ou desatualizados</li>
                <li><strong>Anonimização, bloqueio ou eliminação:</strong> Solicitar remoção de dados desnecessários</li>
                <li><strong>Portabilidade:</strong> Receber seus dados em formato estruturado</li>
                <li><strong>Eliminação:</strong> Solicitar exclusão de dados tratados com consentimento</li>
                <li><strong>Revogação de consentimento:</strong> Retirar seu consentimento a qualquer momento</li>
                <li><strong>Informação sobre compartilhamento:</strong> Saber com quem compartilhamos seus dados</li>
                <li><strong>Oposição:</strong> Opor-se ao tratamento de dados em certas situações</li>
              </ul>
              <p className="text-gray-700 leading-relaxed mb-4 mt-4">
                Para exercer seus direitos, entre em contato conosco através do email de suporte ou pelo assistente virtual.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">9. Cookies e Tecnologias Similares</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                Utilizamos cookies e tecnologias similares para:
              </p>
              <ul className="list-disc list-inside text-gray-700 space-y-2 mb-4 ml-4">
                <li>Manter sua sessão ativa</li>
                <li>Lembrar suas preferências</li>
                <li>Melhorar a experiência de uso</li>
                <li>Analisar o uso do sistema (de forma anonimizada)</li>
              </ul>
              <p className="text-gray-700 leading-relaxed mb-4 mt-4">
                Você pode gerenciar cookies através das configurações do seu navegador.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">10. Transferência Internacional de Dados</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                Seus dados são armazenados em servidores localizados no Brasil. Caso seja necessário transferir dados 
                para outros países, garantiremos que medidas adequadas de proteção sejam implementadas, em conformidade 
                com a LGPD.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">11. Menores de Idade</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                O EconomizeIA não é destinado a menores de 18 anos. Não coletamos intencionalmente dados de menores sem 
                consentimento dos pais ou responsáveis legais. Se tomarmos conhecimento de que coletamos dados de um menor, 
                tomaremos medidas para excluir essas informações.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">12. Alterações nesta Política</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                Podemos atualizar esta Política de Privacidade periodicamente. Alterações significativas serão comunicadas 
                através do email cadastrado ou por meio de notificação no sistema. Recomendamos que revise esta política 
                regularmente.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">13. Encarregado de Proteção de Dados (DPO)</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                Para questões relacionadas à proteção de dados pessoais, você pode entrar em contato com nosso encarregado 
                através do email de suporte ou pelo assistente virtual disponível no sistema.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">14. Contato</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                Para exercer seus direitos, fazer perguntas ou apresentar reclamações sobre o tratamento de seus dados pessoais, 
                entre em contato conosco:
              </p>
              <ul className="list-none text-gray-700 space-y-2 mb-4 ml-4">
                <li><strong>Email:</strong> suporte@economizeia.com</li>
                <li><strong>Assistente Virtual:</strong> Disponível no sistema</li>
                <li><strong>Horário de Atendimento:</strong> Segunda a Sexta, 9h às 18h</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">15. Autoridade Supervisora</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                Você tem o direito de apresentar uma reclamação à Autoridade Nacional de Proteção de Dados (ANPD) se considerar 
                que o tratamento de seus dados pessoais viola a LGPD. Para mais informações, acesse: 
                <a href="https://www.gov.br/anpd" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline ml-1">
                  www.gov.br/anpd
                </a>
              </p>
            </section>

          </div>

          {/* Footer */}
          <div className="mt-12 pt-8 border-t border-gray-200">
            <div className="flex flex-col sm:flex-row justify-between items-center">
              <p className="text-sm text-gray-600 mb-4 sm:mb-0">
                Esta política está em conformidade com a LGPD (Lei nº 13.709/2018).
              </p>
              <div className="flex space-x-4">
                <Link
                  to="/termos"
                  className="text-sm text-gray-600 hover:text-gray-900 font-medium transition-colors"
                >
                  Termos de Uso
                </Link>
                <Link
                  to="/register"
                  className="text-sm text-gray-600 hover:text-gray-900 font-medium transition-colors"
                >
                  Voltar para Registro
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

