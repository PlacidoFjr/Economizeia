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
                <p className="text-gray-600 mt-1">Ãšltima atualizaÃ§Ã£o: 04 de dezembro de 2024</p>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="prose prose-lg max-w-none">
            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">1. AceitaÃ§Ã£o dos Termos</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                Ao acessar e usar o EconomizeIA, vocÃª concorda em cumprir e estar vinculado aos seguintes termos e condiÃ§Ãµes de uso.
                Se vocÃª nÃ£o concorda com alguma parte destes termos, nÃ£o deve usar nosso serviÃ§o.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">2. DescriÃ§Ã£o do ServiÃ§o</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                O EconomizeIA Ã© uma plataforma de gestÃ£o financeira pessoal que oferece:
              </p>
              <ul className="list-disc list-inside text-gray-700 space-y-2 mb-4 ml-4">
                <li>Registro manual e assistido de receitas, despesas, pagamentos e parcelamentos</li>
                <li>Dashboard com visualizaÃ§Ã£o de receitas, despesas e relatÃ³rios financeiros</li>
                <li>Agendamento de pagamentos e lembretes automÃ¡ticos</li>
                <li>Assistente virtual para auxiliar na gestÃ£o financeira</li>
                <li>CategorizaÃ§Ã£o automÃ¡tica de despesas</li>
                <li>NotificaÃ§Ãµes por email, SMS e push (quando configurado)</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">3. Cadastro e Conta de UsuÃ¡rio</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                Para usar o EconomizeIA, vocÃª precisa criar uma conta fornecendo informaÃ§Ãµes precisas e atualizadas. VocÃª Ã© responsÃ¡vel por:
              </p>
              <ul className="list-disc list-inside text-gray-700 space-y-2 mb-4 ml-4">
                <li>Manter a confidencialidade de sua senha</li>
                <li>Notificar-nos imediatamente sobre qualquer uso nÃ£o autorizado de sua conta</li>
                <li>Garantir que todas as informaÃ§Ãµes fornecidas sejam precisas e atualizadas</li>
                <li>Ter pelo menos 18 anos de idade ou ter autorizaÃ§Ã£o de um responsÃ¡vel legal</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">4. Uso AceitÃ¡vel</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                VocÃª concorda em usar o EconomizeIA apenas para fins legais e de acordo com estes Termos. VocÃª nÃ£o deve:
              </p>
              <ul className="list-disc list-inside text-gray-700 space-y-2 mb-4 ml-4">
                <li>Usar o serviÃ§o para atividades ilegais ou nÃ£o autorizadas</li>
                <li>Tentar acessar Ã¡reas restritas do sistema sem autorizaÃ§Ã£o</li>
                <li>Interferir ou interromper o funcionamento do serviÃ§o</li>
                <li>Transmitir vÃ­rus, malware ou cÃ³digo malicioso</li>
                <li>Usar robÃ´s, scripts ou mÃ©todos automatizados para acessar o serviÃ§o</li>
                <li>Copiar, modificar ou distribuir o conteÃºdo do EconomizeIA sem autorizaÃ§Ã£o</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">5. Dados e Privacidade</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                Seus dados pessoais e financeiros sÃ£o tratados de acordo com nossa PolÃ­tica de Privacidade e em conformidade
                com a Lei Geral de ProteÃ§Ã£o de Dados (LGPD). Ao usar o EconomizeIA, vocÃª consente com a coleta, uso e armazenamento
                de suas informaÃ§Ãµes conforme descrito na PolÃ­tica de Privacidade.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">6. PrecisÃ£o das InformaÃ§Ãµes</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                VocÃª Ã© responsÃ¡vel por revisar e confirmar a precisÃ£o dos lanÃ§amentos financeiros registrados no sistema.
                O EconomizeIA nÃ£o se responsabiliza por erros decorrentes de informaÃ§Ãµes incorretas fornecidas pelo usuÃ¡rio.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">7. Disponibilidade do ServiÃ§o</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                Nos esforÃ§amos para manter o EconomizeIA disponÃ­vel 24/7, mas nÃ£o garantimos disponibilidade ininterrupta.
                Podemos realizar manutenÃ§Ãµes programadas ou de emergÃªncia que podem resultar em indisponibilidade temporÃ¡ria.
                NÃ£o nos responsabilizamos por perdas decorrentes de indisponibilidade do serviÃ§o.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">8. Propriedade Intelectual</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                Todo o conteÃºdo do EconomizeIA, incluindo design, logotipos, textos, grÃ¡ficos, cÃ³digo-fonte e software,
                Ã© propriedade do EconomizeIA ou de seus licenciadores e estÃ¡ protegido por leis de direitos autorais e propriedade intelectual.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">9. LimitaÃ§Ã£o de Responsabilidade</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                O EconomizeIA Ã© fornecido "como estÃ¡", sem garantias expressas ou implÃ­citas. NÃ£o nos responsabilizamos por:
              </p>
              <ul className="list-disc list-inside text-gray-700 space-y-2 mb-4 ml-4">
                <li>Perdas financeiras decorrentes do uso ou incapacidade de usar o serviÃ§o</li>
                <li>Erros ou omissÃµes no processamento de dados</li>
                <li>InterrupÃ§Ãµes ou falhas no serviÃ§o</li>
                <li>DecisÃµes financeiras tomadas com base nas informaÃ§Ãµes do sistema</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">10. ModificaÃ§Ãµes dos Termos</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                Reservamos o direito de modificar estes Termos de Uso a qualquer momento. AlteraÃ§Ãµes significativas serÃ£o
                comunicadas atravÃ©s do email cadastrado ou por meio de notificaÃ§Ã£o no sistema. O uso continuado do serviÃ§o
                apÃ³s as modificaÃ§Ãµes constitui aceitaÃ§Ã£o dos novos termos.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">11. Encerramento de Conta</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                VocÃª pode encerrar sua conta a qualquer momento atravÃ©s das configuraÃ§Ãµes do perfil. TambÃ©m reservamos o direito
                de suspender ou encerrar contas que violem estes Termos de Uso, sem aviso prÃ©vio.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">12. Lei AplicÃ¡vel</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                Estes Termos de Uso sÃ£o regidos pelas leis brasileiras. Qualquer disputa serÃ¡ resolvida nos tribunais
                competentes do Brasil.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">13. Contato</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                Para questÃµes sobre estes Termos de Uso, entre em contato conosco atravÃ©s do email de suporte ou pelo
                assistente virtual disponÃ­vel no sistema.
              </p>
            </section>

          </div>

          {/* Footer */}
          <div className="mt-12 pt-8 border-t border-gray-200">
            <div className="flex flex-col sm:flex-row justify-between items-center">
              <p className="text-sm text-gray-600 mb-4 sm:mb-0">
                Ao usar o EconomizeIA, vocÃª concorda com estes Termos de Uso.
              </p>
              <div className="flex space-x-4">
                <Link
                  to="/privacidade"
                  className="text-sm text-gray-600 hover:text-gray-900 font-medium transition-colors"
                >
                  PolÃ­tica de Privacidade
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

