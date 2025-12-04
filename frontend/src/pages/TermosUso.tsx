import { Link } from 'react-router-dom'
import { FileText, ArrowLeft } from 'lucide-react'

export default function TermosUso() {
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
                <FileText className="w-8 h-8 text-gray-700" />
              </div>
              <div>
                <h1 className="text-4xl font-bold text-gray-900">Termos de Uso</h1>
                <p className="text-gray-600 mt-1">Última atualização: 04 de dezembro de 2024</p>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="prose prose-lg max-w-none">
            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">1. Aceitação dos Termos</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                Ao acessar e usar o EconomizeIA, você concorda em cumprir e estar vinculado aos seguintes termos e condições de uso. 
                Se você não concorda com alguma parte destes termos, não deve usar nosso serviço.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">2. Descrição do Serviço</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                O EconomizeIA é uma plataforma de gestão financeira pessoal que oferece:
              </p>
              <ul className="list-disc list-inside text-gray-700 space-y-2 mb-4 ml-4">
                <li>Upload e processamento automático de boletos e faturas através de OCR e inteligência artificial</li>
                <li>Dashboard com visualização de receitas, despesas e relatórios financeiros</li>
                <li>Agendamento de pagamentos e lembretes automáticos</li>
                <li>Assistente virtual para auxiliar na gestão financeira</li>
                <li>Categorização automática de despesas</li>
                <li>Notificações por email, SMS e push (quando configurado)</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">3. Cadastro e Conta de Usuário</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                Para usar o EconomizeIA, você precisa criar uma conta fornecendo informações precisas e atualizadas. Você é responsável por:
              </p>
              <ul className="list-disc list-inside text-gray-700 space-y-2 mb-4 ml-4">
                <li>Manter a confidencialidade de sua senha</li>
                <li>Notificar-nos imediatamente sobre qualquer uso não autorizado de sua conta</li>
                <li>Garantir que todas as informações fornecidas sejam precisas e atualizadas</li>
                <li>Ter pelo menos 18 anos de idade ou ter autorização de um responsável legal</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">4. Uso Aceitável</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                Você concorda em usar o EconomizeIA apenas para fins legais e de acordo com estes Termos. Você não deve:
              </p>
              <ul className="list-disc list-inside text-gray-700 space-y-2 mb-4 ml-4">
                <li>Usar o serviço para atividades ilegais ou não autorizadas</li>
                <li>Tentar acessar áreas restritas do sistema sem autorização</li>
                <li>Interferir ou interromper o funcionamento do serviço</li>
                <li>Transmitir vírus, malware ou código malicioso</li>
                <li>Usar robôs, scripts ou métodos automatizados para acessar o serviço</li>
                <li>Copiar, modificar ou distribuir o conteúdo do EconomizeIA sem autorização</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">5. Dados e Privacidade</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                Seus dados pessoais e financeiros são tratados de acordo com nossa Política de Privacidade e em conformidade 
                com a Lei Geral de Proteção de Dados (LGPD). Ao usar o EconomizeIA, você consente com a coleta, uso e armazenamento 
                de suas informações conforme descrito na Política de Privacidade.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">6. Precisão das Informações</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                Embora utilizemos tecnologias avançadas de OCR e IA para extrair informações de boletos, você é responsável 
                por revisar e confirmar a precisão dos dados extraídos. O EconomizeIA não se responsabiliza por erros decorrentes 
                de informações incorretas fornecidas pelo usuário ou extraídas incorretamente de documentos.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">7. Disponibilidade do Serviço</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                Nos esforçamos para manter o EconomizeIA disponível 24/7, mas não garantimos disponibilidade ininterrupta. 
                Podemos realizar manutenções programadas ou de emergência que podem resultar em indisponibilidade temporária. 
                Não nos responsabilizamos por perdas decorrentes de indisponibilidade do serviço.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">8. Propriedade Intelectual</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                Todo o conteúdo do EconomizeIA, incluindo design, logotipos, textos, gráficos, código-fonte e software, 
                é propriedade do EconomizeIA ou de seus licenciadores e está protegido por leis de direitos autorais e propriedade intelectual.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">9. Limitação de Responsabilidade</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                O EconomizeIA é fornecido "como está", sem garantias expressas ou implícitas. Não nos responsabilizamos por:
              </p>
              <ul className="list-disc list-inside text-gray-700 space-y-2 mb-4 ml-4">
                <li>Perdas financeiras decorrentes do uso ou incapacidade de usar o serviço</li>
                <li>Erros ou omissões no processamento de dados</li>
                <li>Interrupções ou falhas no serviço</li>
                <li>Decisões financeiras tomadas com base nas informações do sistema</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">10. Modificações dos Termos</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                Reservamos o direito de modificar estes Termos de Uso a qualquer momento. Alterações significativas serão 
                comunicadas através do email cadastrado ou por meio de notificação no sistema. O uso continuado do serviço 
                após as modificações constitui aceitação dos novos termos.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">11. Encerramento de Conta</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                Você pode encerrar sua conta a qualquer momento através das configurações do perfil. Também reservamos o direito 
                de suspender ou encerrar contas que violem estes Termos de Uso, sem aviso prévio.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">12. Lei Aplicável</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                Estes Termos de Uso são regidos pelas leis brasileiras. Qualquer disputa será resolvida nos tribunais 
                competentes do Brasil.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">13. Contato</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                Para questões sobre estes Termos de Uso, entre em contato conosco através do email de suporte ou pelo 
                assistente virtual disponível no sistema.
              </p>
            </section>

          </div>

          {/* Footer */}
          <div className="mt-12 pt-8 border-t border-gray-200">
            <div className="flex flex-col sm:flex-row justify-between items-center">
              <p className="text-sm text-gray-600 mb-4 sm:mb-0">
                Ao usar o EconomizeIA, você concorda com estes Termos de Uso.
              </p>
              <div className="flex space-x-4">
                <Link
                  to="/privacidade"
                  className="text-sm text-gray-600 hover:text-gray-900 font-medium transition-colors"
                >
                  Política de Privacidade
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

