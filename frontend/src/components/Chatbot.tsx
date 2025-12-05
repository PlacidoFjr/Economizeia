import { useState, useRef, useEffect } from 'react'
import { MessageCircle, X, Send, Bot, User, Trash2 } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'
import api from '../services/api'

interface Message {
  id: string
  text: string
  sender: 'user' | 'bot'
  timestamp: Date
}

const INITIAL_MESSAGES: Message[] = [
  {
    id: '1',
    text: 'Olá! Sou o assistente virtual do EconomizeIA. Como posso ajudá-lo hoje?',
    sender: 'bot',
    timestamp: new Date(),
  },
]

const QUICK_QUESTIONS = [
  'Quantos boletos eu tenho?',
  'Quanto tenho pendente?',
  'Como adicionar uma despesa?',
  'Ver meus boletos vencidos',
]

const STORAGE_KEY = 'economizeia_chatbot_messages'

// Função para carregar mensagens do localStorage
const loadMessages = (): Message[] => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      const parsed = JSON.parse(saved)
      // Converter timestamps de string para Date
      return parsed.map((msg: any) => ({
        ...msg,
        timestamp: new Date(msg.timestamp)
      }))
    }
  } catch (error) {
    console.error('Erro ao carregar mensagens do localStorage:', error)
  }
  return INITIAL_MESSAGES
}

// Função para salvar mensagens no localStorage
const saveMessages = (messages: Message[]) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages))
  } catch (error) {
    console.error('Erro ao salvar mensagens no localStorage:', error)
  }
}

export default function Chatbot() {
  const queryClient = useQueryClient()
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>(loadMessages)
  const [inputText, setInputText] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Salvar mensagens no localStorage sempre que mudarem
  useEffect(() => {
    saveMessages(messages)
  }, [messages])

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isOpen])

  const handleQuickQuestion = (question: string) => {
    setInputText(question)
    handleSendMessage(question)
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

      // Chamar API do backend com Ollama
      const response = await api.post('/chatbot/chat', {
        message: messageText,
        conversation_history: conversationHistory
      })
      
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: response.data.response,
        sender: 'bot',
        timestamp: new Date(),
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
          
          console.log('✅ Transação criada! Queries atualizadas:', response.data.action)
        } catch (error) {
          console.error('Erro ao atualizar queries:', error)
        }
      }
    } catch (error: any) {
      console.error('Erro ao chamar chatbot:', error)
      
      // Mensagem de erro mais amigável
      let errorText = 'Desculpe, ocorreu um erro ao processar sua mensagem.'
      
      if (error.response?.status === 500) {
        errorText = 'O servidor de IA não está disponível no momento. Por favor, verifique se o Ollama está rodando e tente novamente em alguns instantes.'
      } else if (error.response?.data?.detail) {
        errorText = error.response.data.detail
      } else if (error.message?.includes('timeout') || error.message?.includes('Network')) {
        errorText = 'A conexão com o servidor de IA está demorando muito. Por favor, tente novamente.'
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

  return (
    <>
      {/* Botão flutuante */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-4 right-4 sm:bottom-6 sm:right-6 w-12 h-12 sm:w-14 sm:h-14 bg-gray-900 text-white rounded-full shadow-lg hover:shadow-xl hover:bg-gray-800 transition-all flex items-center justify-center z-50"
          aria-label="Abrir chatbot"
        >
          <MessageCircle className="w-5 h-5 sm:w-6 sm:h-6" />
        </button>
      )}

      {/* Janela do Chatbot */}
      {isOpen && (
        <div className="fixed inset-0 sm:inset-auto sm:bottom-6 sm:right-6 sm:w-96 sm:h-[600px] bg-white rounded-none sm:rounded-lg shadow-xl border-0 sm:border border-gray-200 flex flex-col z-50 safe-area-inset chatbot-container">
          {/* Header */}
          <div className="bg-gray-900 text-white p-3 sm:p-4 flex items-center justify-between safe-area-top">
            <div className="flex items-center flex-1 min-w-0">
              <div className="bg-gray-800 p-1.5 sm:p-2 rounded mr-2 sm:mr-3 flex-shrink-0">
                <Bot className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
              </div>
              <div className="min-w-0 flex-1">
                <h3 className="font-semibold text-xs sm:text-sm truncate">Assistente EconomizeIA</h3>
                <p className="text-xs text-gray-400">Online</p>
              </div>
            </div>
            <div className="flex items-center space-x-2 sm:space-x-2 flex-shrink-0 ml-2">
              <button
                onClick={() => {
                  if (confirm('Deseja limpar o histórico da conversa?')) {
                    localStorage.removeItem(STORAGE_KEY)
                    setMessages(INITIAL_MESSAGES)
                  }
                }}
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
          <div className="flex-1 overflow-y-auto p-3 sm:p-4 space-y-3 sm:space-y-4 bg-gray-50 overscroll-contain">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
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
                    className={`rounded-lg px-2.5 py-1.5 sm:px-3 sm:py-2 ${
                      message.sender === 'user'
                        ? 'bg-gray-900 text-white'
                        : 'bg-white text-gray-900 border border-gray-200'
                    }`}
                  >
                    <p className="text-xs sm:text-sm whitespace-pre-wrap break-words">{message.text}</p>
                    <p className="text-[10px] sm:text-xs mt-1 opacity-70">
                      {message.timestamp.toLocaleTimeString('pt-BR', {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </p>
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
                  <div className="bg-white rounded-lg sm:rounded-2xl px-3 py-2 sm:px-4 sm:py-3 border border-gray-200">
                    <div className="flex items-center space-x-1.5 sm:space-x-2">
                      <div className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      <span className="text-[10px] sm:text-xs text-gray-500 ml-1.5 sm:ml-2">Pensando...</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Perguntas rápidas */}
          {messages.length === INITIAL_MESSAGES.length && (
            <div className="px-3 sm:px-4 py-2 bg-white border-t border-gray-200">
              <p className="text-[10px] sm:text-xs font-medium text-gray-600 mb-1.5 sm:mb-2">Perguntas rápidas:</p>
              <div className="flex flex-wrap gap-1.5 sm:gap-2">
                {QUICK_QUESTIONS.map((question, index) => (
                  <button
                    key={index}
                    onClick={() => handleQuickQuestion(question)}
                    className="text-[10px] sm:text-xs px-2 sm:px-3 py-1 sm:py-1.5 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 active:bg-gray-300 transition-colors font-medium touch-manipulation"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input */}
          <div className="p-3 sm:p-4 bg-white border-t border-gray-200 safe-area-bottom">
            <div className="flex space-x-2">
              <input
                ref={inputRef}
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Digite sua mensagem..."
                className="flex-1 px-2.5 sm:px-3 py-2 sm:py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500 text-sm sm:text-sm touch-manipulation"
                disabled={isLoading}
                autoComplete="off"
                autoCorrect="off"
                autoCapitalize="off"
                spellCheck="false"
              />
              <button
                onClick={() => handleSendMessage()}
                disabled={!inputText.trim() || isLoading}
                className="px-3 sm:px-4 py-2 bg-gray-900 text-white rounded-md hover:bg-gray-800 active:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center touch-manipulation min-w-[44px]"
                aria-label="Enviar mensagem"
              >
                <Send className="w-4 h-4 sm:w-4 sm:h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

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

