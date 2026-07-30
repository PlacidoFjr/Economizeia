import { useState, useRef, useEffect } from 'react'
import { MessageCircle, X, Send, Bot, User, Trash2, Sparkles, WalletCards } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'motion/react'
import gsap from 'gsap'
import { animate } from 'animejs'
import api from '../services/api'
import ConfirmDialog from './ConfirmDialog'
import { useAuth } from '../contexts/AuthContext'

interface Message {
  id: string
  text: string
  sender: 'user' | 'bot'
  timestamp: Date
  action?: string
  suggestions?: string[]
}

const createInitialMessages = (): Message[] => [
  {
    id: '1',
    text: 'Oi! Posso consultar seus dados e registrar gastos ou receitas. Se faltar detalhe, eu pergunto antes de salvar.',
    sender: 'bot',
    timestamp: new Date(),
  },
]

const QUICK_QUESTIONS = [
  'Gastei R$ 35 no Uber',
  'R$ 200 boleto pago',
  'Quanto tenho pendente?',
  'Recebi R$ 2500 de salário',
]

const DETAIL_SUGGESTIONS = ['Mercado', 'Uber', 'Energia', 'Farmácia']

const LEGACY_STORAGE_KEY = 'economizeia_chatbot_messages_v3'
const LEGACY_STORAGE_PREFIX = 'economizeia_chatbot_messages_v4'
const STORAGE_KEY_PREFIX = 'economizeia_chatbot_messages_v5'

const getStorageKey = (user?: { id?: string; email?: string } | null) => {
  const userKey = user?.id || user?.email
  return userKey ? `${STORAGE_KEY_PREFIX}:${userKey}` : null
}

const clearLegacyChatStorage = () => {
  localStorage.removeItem(LEGACY_STORAGE_KEY)
  Object.keys(localStorage)
    .filter((key) => key.startsWith(`${LEGACY_STORAGE_PREFIX}:`))
    .forEach((key) => localStorage.removeItem(key))
}

// Função para carregar mensagens do localStorage
const loadMessages = (storageKey: string | null): Message[] => {
  if (!storageKey) return createInitialMessages()

  try {
    const saved = localStorage.getItem(storageKey)
    if (saved) {
      const parsed = JSON.parse(saved)
      if (!Array.isArray(parsed)) return createInitialMessages()

      const hasLegacyContent = parsed.some((msg: any) =>
        String(msg.text || '').includes('Como posso ajudá-lo hoje?') ||
        String(msg.text || '').includes('Despesa criada com sucesso no valor de R$ 20.00')
      )
      if (hasLegacyContent) return createInitialMessages()

      const cleanMessages = parsed.filter((msg: any) =>
        msg &&
        (msg.sender === 'user' || msg.sender === 'bot') &&
        typeof msg.text === 'string' &&
        msg.text.trim().length > 0
      )

      if (!cleanMessages.length) return createInitialMessages()

      // Converter timestamps de string para Date
      return cleanMessages.map((msg: any) => ({
        ...msg,
        timestamp: new Date(msg.timestamp)
      }))
    }
  } catch (error) {
    console.error('Erro ao carregar mensagens do localStorage:', error)
  }
  return createInitialMessages()
}

// Função para salvar mensagens no localStorage
const saveMessages = (storageKey: string | null, messages: Message[]) => {
  if (!storageKey) return

  try {
    localStorage.setItem(storageKey, JSON.stringify(messages))
  } catch (error) {
    console.error('Erro ao salvar mensagens no localStorage:', error)
  }
}

export default function Chatbot() {
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const storageKey = getStorageKey(user)
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>(createInitialMessages)
  const [inputText, setInputText] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [clearDialogOpen, setClearDialogOpen] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const panelRef = useRef<HTMLDivElement>(null)
  const launcherRef = useRef<HTMLButtonElement>(null)
  const skipNextSaveRef = useRef(false)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    clearLegacyChatStorage()
    skipNextSaveRef.current = true
    setMessages(loadMessages(storageKey))
  }, [storageKey])

  // Salvar mensagens no localStorage sempre que mudarem
  useEffect(() => {
    if (skipNextSaveRef.current) {
      skipNextSaveRef.current = false
      return
    }
    saveMessages(storageKey, messages)
  }, [messages, storageKey])

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isOpen])

  useEffect(() => {
    if (!isOpen || !panelRef.current) return
    const context = gsap.context(() => {
      gsap.from('.chat-message-row', {
        y: 10,
        opacity: 0,
        duration: 0.24,
        ease: 'power2.out',
        stagger: 0.025,
      })
    }, panelRef)

    return () => context.revert()
  }, [isOpen])

  useEffect(() => {
    if (isOpen || !launcherRef.current) return
    const animation = animate(launcherRef.current, {
      scale: [1, 1.06, 1],
      duration: 1800,
      loop: true,
      ease: 'inOut(2)',
    })

    return () => {
      animation.pause()
    }
  }, [isOpen])

  // Esconder barra de navegação do navegador mobile quando chatbot estiver aberto
  useEffect(() => {
    const isMobile = window.innerWidth < 640 // sm breakpoint do Tailwind
    
    if (isOpen && isMobile) {
      // Adicionar classe ao body para esconder barra de navegação
      document.body.classList.add('chatbot-open-mobile')
      // Forçar altura da viewport para esconder barra de navegação
      const viewportHeight = window.innerHeight
      document.documentElement.style.setProperty('--vh', `${viewportHeight * 0.01}px`)
    } else {
      // Remover classe quando fechar
      document.body.classList.remove('chatbot-open-mobile')
      document.documentElement.style.removeProperty('--vh')
    }

    // Limpar ao desmontar
    return () => {
      document.body.classList.remove('chatbot-open-mobile')
      document.documentElement.style.removeProperty('--vh')
    }
  }, [isOpen])

  const handleQuickQuestion = (question: string) => {
    setInputText(question)
    handleSendMessage(question)
  }

  const getBotSuggestions = (action?: string, text?: string) => {
    const normalizedText = (text || '').toLowerCase()
    if (action === 'ask_for_info' && (normalizedText.includes('com o que') || normalizedText.includes('onde foi'))) {
      return DETAIL_SUGGESTIONS
    }
    if (action === 'ask_for_info' && normalizedText.includes('de onde veio')) {
      return ['Salário', 'Freelance', 'Vendas', 'Reembolso']
    }
    if (action === 'expense_created' || action === 'income_created') {
      return ['Como está meu saldo?', 'Gastos por categoria', 'Quanto tenho pendente?']
    }
    return []
  }

  const handleSendMessage = async (text?: string) => {
    const messageText = text || inputText.trim()
    if (!messageText) return

    // Adiciona mensagem do usuário
    const userMessage: Message = {
      id: Date.now().toString(),
      text: messageText,
      sender: 'user',
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMessage])
    setInputText('')
    setIsLoading(true)

    try {
      // Preparar histórico da conversa (últimas 10 mensagens)
      const conversationHistory = messages
        .slice(-10)
        .map(msg => ({
          sender: msg.sender,
          text: msg.text
        }))

      // Chamar API do backend
      const response = await api.post('/chatbot/chat', {
        message: messageText,
        conversation_history: conversationHistory
      })
      
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: response.data.response,
        sender: 'bot',
        timestamp: new Date(),
        action: response.data.action,
        suggestions: getBotSuggestions(response.data.action, response.data.response),
      }
      
      setMessages((prev) => [...prev, botMessage])
      setIsLoading(false)

      // Se uma transação foi criada (despesa ou receita), invalidar queries para atualizar o dashboard
      if (response.data.action === 'expense_created' || response.data.action === 'income_created') {
        try {
          // Invalidar todas as queries relacionadas
          await Promise.all([
            queryClient.invalidateQueries({ queryKey: ['bills'] }),
            queryClient.invalidateQueries({ queryKey: ['finances'] }),
            queryClient.invalidateQueries({ queryKey: ['dashboard'] }),
          ])
          
          // Forçar refetch imediato das queries críticas
          await Promise.all([
            queryClient.refetchQueries({ queryKey: ['bills'], exact: false }),
            queryClient.refetchQueries({ queryKey: ['finances'], exact: false }),
          ])
          
        } catch (error) {
          console.error('Erro ao atualizar queries:', error)
        }
      }
    } catch (error: any) {
      console.error('Erro ao chamar chatbot:', error)
      
      // Mensagem de erro mais amigável
      let errorText = 'Desculpe, ocorreu um erro ao processar sua mensagem.'
      
      if (error.response?.status === 429) {
        // Limite de uso atingido
        errorText = error.response.data.detail || 'Limite de mensagens do chatbot atingido este mês. O limite será resetado no próximo mês.'
      } else if (error.response?.status === 500) {
        errorText = 'O assistente não está disponível no momento. Tente novamente em alguns instantes.'
      } else if (error.response?.data?.detail) {
        errorText = error.response.data.detail
      } else if (error.message?.includes('timeout') || error.message?.includes('Network')) {
        errorText = 'A conexão com o assistente está demorando muito. Por favor, tente novamente.'
      } else {
        errorText = 'Desculpe, ocorreu um erro. Por favor, tente novamente ou use as funcionalidades do menu.'
      }
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: errorText,
        sender: 'bot',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const clearConversation = () => {
    if (storageKey) {
      localStorage.removeItem(storageKey)
    }
    localStorage.removeItem(LEGACY_STORAGE_KEY)
    setMessages(createInitialMessages())
    setClearDialogOpen(false)
  }

  return (
    <>
      <ConfirmDialog
        open={clearDialogOpen}
        title="Limpar conversa?"
        description="O histórico atual do assistente será apagado deste navegador. Seus lançamentos financeiros não serão removidos."
        confirmLabel="Limpar"
        tone="danger"
        onCancel={() => setClearDialogOpen(false)}
        onConfirm={clearConversation}
      />
      {/* Botão flutuante */}
      {!isOpen && (
        <button
          ref={launcherRef}
          onClick={() => setIsOpen(true)}
          className="fixed bottom-20 right-4 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-slate-950 text-white shadow-xl shadow-slate-400/40 transition-all hover:bg-slate-800 sm:bottom-6 sm:right-6 sm:h-14 sm:w-14"
          aria-label="Abrir chatbot"
        >
          <MessageCircle className="h-6 w-6" />
        </button>
      )}

      {/* Janela do Chatbot */}
      <AnimatePresence>
      {isOpen && (
        <motion.div
          ref={panelRef}
          initial={{ opacity: 0, y: 22, scale: 0.97 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 18, scale: 0.98 }}
          transition={{ duration: 0.22, ease: 'easeOut' }}
          className="chatbot-container safe-area-inset fixed inset-0 z-50 flex flex-col border-0 border-slate-200 bg-white shadow-2xl dark:border-slate-800 dark:bg-slate-950 sm:inset-auto sm:bottom-6 sm:right-6 sm:h-[640px] sm:w-[420px] sm:rounded-lg sm:border"
        >
          {/* Header */}
          <div className="relative flex items-center justify-between bg-slate-950 p-3 text-white safe-area-top sm:p-4">
            <div className="flex items-center flex-1 min-w-0">
              <div className="mr-2 flex-shrink-0 rounded-md bg-cyan-300/12 p-2 sm:mr-3">
                <Bot className="h-4 w-4 text-cyan-300" />
              </div>
              <div className="min-w-0 flex-1">
                <h3 className="font-semibold text-xs sm:text-sm truncate">Assistente EconomizeIA</h3>
                <p className="flex items-center gap-1 text-xs text-slate-400 whitespace-nowrap">
                  <Sparkles className="h-3 w-3 text-cyan-300" />
                  Organiza antes de salvar
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2 sm:space-x-2 flex-shrink-0 ml-2">
              <button
                onClick={() => setClearDialogOpen(true)}
                className="hover:bg-gray-800 active:bg-gray-700 p-2 sm:p-1.5 rounded transition-colors touch-manipulation min-w-[44px] min-h-[44px] sm:min-w-0 sm:min-h-0 flex items-center justify-center"
                aria-label="Limpar conversa"
                title="Limpar conversa"
              >
                <Trash2 className="w-5 h-5 sm:w-4 sm:h-4 text-white" />
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="hover:bg-gray-800 active:bg-gray-700 p-2 sm:p-1.5 rounded transition-colors touch-manipulation min-w-[44px] min-h-[44px] sm:min-w-0 sm:min-h-0 flex items-center justify-center"
                aria-label="Fechar chatbot"
              >
                <X className="w-5 h-5 sm:w-4 sm:h-4 text-white" />
              </button>
            </div>
          </div>

          {/* Mensagens */}
          <div className="flex-1 overflow-y-auto bg-slate-50 p-3 sm:p-4 space-y-3 sm:space-y-4 overscroll-contain dark:bg-slate-950">
            {messages.filter((message) => message.text.trim().length > 0).map((message) => (
              <div
                key={message.id}
                className={`chat-message-row flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`flex items-start space-x-2 sm:space-x-2 max-w-[85%] sm:max-w-[80%] ${
                    message.sender === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                  }`}
                >
                  <div
                    className={`flex-shrink-0 w-6 h-6 sm:w-7 sm:h-7 rounded-full flex items-center justify-center ${
                      message.sender === 'user'
                        ? 'bg-gray-900'
                        : 'bg-gray-200'
                    }`}
                  >
                    {message.sender === 'user' ? (
                      <User className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-white" />
                    ) : (
                      <Bot className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-gray-700" />
                    )}
                  </div>
                  <div
                    className={`rounded-lg px-3 py-2 shadow-sm sm:px-3.5 sm:py-2.5 ${
                      message.sender === 'user'
                        ? 'bg-slate-950 text-white'
                        : 'border border-slate-200 bg-white text-slate-900 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-100'
                    }`}
                  >
                    <p className="text-xs sm:text-sm whitespace-pre-wrap break-words">{message.text}</p>
                    <p className="text-[10px] sm:text-xs mt-1 opacity-70">
                      {message.timestamp.toLocaleTimeString('pt-BR', {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </p>
                    {message.sender === 'bot' && !!message.suggestions?.length && (
                      <div className="mt-3 flex flex-wrap gap-1.5">
                        {message.suggestions.map((suggestion) => (
                          <button
                            key={suggestion}
                            type="button"
                            onClick={() => handleQuickQuestion(suggestion)}
                            className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-[11px] font-semibold text-slate-700 transition-colors hover:border-slate-300 hover:bg-white dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:border-slate-600 dark:hover:bg-slate-900"
                          >
                            {suggestion}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex justify-start">
                <div className="flex items-start space-x-2">
                  <div className="flex-shrink-0 w-6 h-6 sm:w-8 sm:h-8 rounded-full bg-gray-200 flex items-center justify-center">
                    <Bot className="w-3.5 h-3.5 sm:w-5 sm:h-5 text-gray-700 animate-pulse" />
                  </div>
                  <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 dark:border-slate-800 dark:bg-slate-900 sm:rounded-2xl sm:px-4 sm:py-3">
                    <div className="flex items-center space-x-1.5 sm:space-x-2">
                      <div className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      <span className="ml-1.5 text-[10px] text-gray-500 dark:text-slate-400 sm:ml-2 sm:text-xs">Pensando...</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Perguntas rápidas */}
          {messages.length === 1 && (
            <div className="border-t border-slate-200 bg-white px-3 py-3 dark:border-slate-800 dark:bg-slate-950 sm:px-4">
              <p className="mb-2 flex items-center gap-1.5 text-[11px] font-semibold text-slate-600 dark:text-slate-300">
                <WalletCards className="h-3.5 w-3.5" />
                Atalhos úteis
              </p>
              <div className="flex flex-wrap gap-1.5 sm:gap-2">
                {QUICK_QUESTIONS.map((question, index) => (
                  <button
                    key={index}
                    onClick={() => handleQuickQuestion(question)}
                    className="touch-manipulation rounded-full bg-slate-100 px-3 py-1.5 text-[11px] font-semibold text-slate-700 transition-colors hover:bg-slate-200 active:bg-slate-300 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input */}
          <div className="safe-area-bottom border-t border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-950 sm:p-4">
            <div className="flex space-x-2">
              <input
                ref={inputRef}
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Digite sua mensagem..."
                className="touch-manipulation min-h-[44px] flex-1 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-950 focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-white dark:placeholder:text-slate-500"
                disabled={isLoading}
                autoComplete="off"
                autoCorrect="off"
                autoCapitalize="off"
                spellCheck="false"
              />
              <button
                onClick={() => handleSendMessage()}
                disabled={!inputText.trim() || isLoading}
                className="flex min-w-[44px] items-center justify-center rounded-lg bg-slate-950 px-3 py-2 text-white transition-colors hover:bg-slate-800 active:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50 touch-manipulation sm:px-4"
                aria-label="Enviar mensagem"
              >
                <Send className="w-4 h-4 sm:w-4 sm:h-4" />
              </button>
            </div>
          </div>
        </motion.div>
      )}
      </AnimatePresence>

      <style>{`
        @keyframes slide-up {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-slide-up {
          animation: slide-up 0.3s ease-out;
        }
      `}</style>
    </>
  )
}

