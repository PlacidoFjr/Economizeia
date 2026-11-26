import { useState, useRef, useEffect } from 'react'
import { MessageCircle, X, Send, Bot, User, Trash2, Sparkles, WalletCards } from 'lucide-react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'motion/react'
import api from '../services/api'
import ConfirmDialog from './ConfirmDialog'
import QuickEntryForm, { type QuickEntry } from './QuickEntryForm'
import { useAuth } from '../contexts/AuthContext'

interface Message {
  id: string
  text: string
  sender: 'user' | 'bot'
  timestamp: Date
}

const createInitialMessages = (): Message[] => [
  {
    id: '1',
    text: 'Oi! Posso organizar uma lista de receitas, gastos próprios, despesas pagas por terceiros, limites e metas. Envie um item por linha. Mostro o rascunho antes de salvar.',
    sender: 'bot',
    timestamp: new Date(),
  },
]

const QUICK_QUESTIONS = [
  'Gastei R$ 35 no Uber',
  'Academia: R$ 150/mês, paga pelo meu pai',
  'Meu planejamento mensal',
  'Recebi R$ 2500 de salário',
]

type ChatResult = { response: string; action: string; draft_id?: string | null }
type ChatTurn = { id: string; message: string; result: ChatResult; created_at: string }
type ChatHistory = { turns: ChatTurn[]; draft: ChatResult | null }
type ChatRequest = { message: string; request_id: string; draft_id?: string; entry?: QuickEntry }

function ChatMessageText({ text }: { text: string }) {
  const sections = text.split('\n\n')
  if (text.length <= 450 || sections.length < 2) {
    return <p className="whitespace-pre-wrap break-words text-sm">{text}</p>
  }
  return (
    <div className="text-sm">
      <p className="font-semibold">{sections[0]}</p>
      <details className="mt-2">
        <summary className="cursor-pointer font-medium underline underline-offset-4">Ver detalhes</summary>
        <p className="mt-2 whitespace-pre-wrap break-words">{sections.slice(1).join('\n\n')}</p>
      </details>
    </div>
  )
}

export default function Chatbot() {
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const historyKey = ['financial-chat-history', user?.id]
  const [isOpen, setIsOpen] = useState(false)
  const [inputText, setInputText] = useState('')
  const [quickKind, setQuickKind] = useState<QuickEntry['kind'] | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [clearDialogOpen, setClearDialogOpen] = useState(false)
  const [sending, setSending] = useState<ChatRequest | null>(null)
  const [failed, setFailed] = useState<{ message: string; retry?: ChatRequest } | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const launcherRef = useRef<HTMLButtonElement>(null)
  const inFlight = useRef(false)

  const history = useQuery({
    queryKey: historyKey,
    queryFn: async () => (await api.get<ChatHistory>('/chatbot/history')).data,
    enabled: isOpen && !!user,
    retry: false,
    gcTime: 0,
  })
  const draft = history.data?.draft
  const turns = history.data?.turns ?? []
  const messages: Message[] = [...createInitialMessages(), ...turns.flatMap(turn => [
    { id: turn.id + '-user', text: turn.message, sender: 'user' as const, timestamp: new Date(turn.created_at) },
    { id: turn.id + '-bot', text: turn.result.response, sender: 'bot' as const, timestamp: new Date(turn.created_at) },
  ])]

  useEffect(() => {
    if (isOpen && !history.isPending) inputRef.current?.focus()
  }, [isOpen, history.isPending])

  const closeChat = () => {
    setIsOpen(false)
    setQuickKind(null)
    requestAnimationFrame(() => launcherRef.current?.focus())
  }

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ block: 'end' })
  }, [isOpen, history.data, sending, failed])

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

  const submit = async (request: ChatRequest) => {
    if (inFlight.current) return
    inFlight.current = true
    setIsLoading(true)
    setSending(request)
    setFailed(null)
    try {
      const { data } = await api.post<ChatResult>('/chatbot/chat', request)
      queryClient.setQueryData<ChatHistory>(historyKey, (previous) => ({
        turns: [...(previous?.turns ?? []).filter(turn => turn.id !== request.request_id),
          { id: request.request_id, message: request.message, result: data, created_at: new Date().toISOString() }].slice(-50),
        draft: data.draft_id ? data : previous?.draft ?? null,
      }))
      const updates = [history.refetch()]
      if (['transactions_created', 'expense_created', 'income_created'].includes(data.action)) {
        await Promise.all([
          ...updates,
          ...['bills', 'finances', 'financial-overview', 'financial-plan-items', 'savings-goals', 'payments', 'installment-bills']
            .map(key => queryClient.invalidateQueries({ queryKey: [key] })),
        ])
      } else {
        await Promise.all(updates)
      }
    } catch (error: unknown) {
      const response = (error as { response?: { status?: number; data?: { detail?: unknown } } }).response
      const detail = response?.data?.detail
      const retry = !response?.status || response.status >= 500
      setFailed({
        message: typeof detail === 'string' ? detail : 'Não foi possível confirmar a resposta do assistente.',
        retry: retry ? request : undefined,
      })
      if (!retry) {
        await history.refetch()
        if (response?.status !== 409) setInputText(request.message)
      }
    } finally {
      setSending(null)
      setIsLoading(false)
      inFlight.current = false
    }
  }

  const handleSendMessage = (text?: string, draftId?: string) => {
    const message = (text ?? inputText).trim()
    if (!message || inFlight.current || history.isPending || history.isError) return
    setInputText('')
    void submit({ message, request_id: crypto.randomUUID(), draft_id: draftId ?? draft?.draft_id ?? 'none' })
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const clearConversation = async () => {
    if (inFlight.current) return
    inFlight.current = true
    setIsLoading(true)
    try {
      await api.delete('/chatbot/history')
      queryClient.setQueryData<ChatHistory>(historyKey, { turns: [], draft: null })
      setFailed(null)
    } catch {
      setFailed({ message: 'Não foi possível limpar a conversa. Tente novamente.' })
    } finally {
      setIsLoading(false)
      inFlight.current = false
      setClearDialogOpen(false)
    }
  }

  return (
    <>
      <ConfirmDialog
        open={clearDialogOpen}
        title="Limpar conversa?"
        description="O histórico da conversa e o rascunho pendente serão removidos da sua conta."
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
          initial={{ opacity: 0, y: 22, scale: 0.97 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 18, scale: 0.98 }}
          transition={{ duration: 0.22, ease: 'easeOut' }}
          className="chatbot-container safe-area-inset fixed inset-0 z-[110] flex flex-col border-0 border-slate-200 bg-white shadow-2xl dark:border-slate-800 dark:bg-slate-950 sm:inset-auto sm:bottom-6 sm:right-6 sm:z-[70] sm:h-[min(760px,90vh)] sm:w-[520px] sm:rounded-lg sm:border"
          role="dialog"
          aria-labelledby="financial-chat-title"
          onKeyDown={(event) => {
            if (event.key === 'Escape' && !clearDialogOpen) closeChat()
          }}
        >
          {/* Header */}
          <div className="relative flex items-center justify-between bg-slate-950 p-3 text-white safe-area-top sm:p-4">
            <div className="flex items-center flex-1 min-w-0">
              <div className="mr-2 flex-shrink-0 rounded-md bg-cyan-300/12 p-2 sm:mr-3">
                <Bot className="h-4 w-4 text-cyan-300" />
              </div>
              <div className="min-w-0 flex-1">
                <h3 id="financial-chat-title" className="font-semibold text-xs sm:text-sm truncate">Assistente EconomizeIA</h3>
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
                onClick={closeChat}
                className="hover:bg-gray-800 active:bg-gray-700 p-2 sm:p-1.5 rounded transition-colors touch-manipulation min-w-[44px] min-h-[44px] sm:min-w-0 sm:min-h-0 flex items-center justify-center"
                aria-label="Fechar chatbot"
              >
                <X className="w-5 h-5 sm:w-4 sm:h-4 text-white" />
              </button>
            </div>
          </div>

          {/* Mensagens */}
          <div className="flex-1 overflow-y-auto bg-slate-50 p-3 sm:p-4 space-y-3 sm:space-y-4 overscroll-contain dark:bg-slate-950" role="log" aria-live="polite">
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
                    <ChatMessageText text={message.text} />
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

            {history.isPending && <p className="text-sm text-slate-600">Carregando conversa...</p>}
            {history.isError && (
              <div className="text-sm" role="alert">
                <p>Não foi possível carregar a conversa.</p>
                <button className="mt-1 font-semibold underline" onClick={() => history.refetch()}>Tentar novamente</button>
              </div>
            )}
            {sending && <p className="ml-auto w-fit max-w-[80%] whitespace-pre-wrap break-words rounded-lg bg-slate-900 px-3 py-2 text-sm text-white">{sending.message}</p>}
            {failed && (
              <div className="text-sm" role="alert">
                <p>{failed.message}</p>
                {failed.retry && <button className="mt-1 font-semibold underline" onClick={() => failed.retry && submit(failed.retry)}>Tentar a mesma mensagem</button>}
              </div>
            )}

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

          {draft?.draft_id && (
            <section aria-label="Rascunho pendente" className="border-t border-teal-200 bg-teal-50 px-3 py-3 text-sm text-teal-950 dark:border-teal-800 dark:bg-teal-950 dark:text-teal-50 sm:px-4">
              <details open={draft.action !== 'confirm_transactions' || undefined}>
                <summary className="cursor-pointer font-semibold">{draft.action === 'confirm_transactions' ? 'Revisar rascunho pendente' : 'Completar rascunho'}</summary>
                <p className="mt-2 max-h-32 overflow-y-auto whitespace-pre-wrap break-words">{draft.response}</p>
              </details>
              <div className="mt-2 flex flex-wrap gap-2">
                {draft.action === 'confirm_transactions' && <button disabled={isLoading} className="rounded-md bg-teal-800 px-3 py-2 font-semibold text-white disabled:opacity-50" onClick={() => handleSendMessage('Confirmar lançamentos', draft.draft_id ?? undefined)}>Confirmar</button>}
                <button disabled={isLoading} className="rounded-md border border-teal-600 px-3 py-2 font-semibold disabled:opacity-50" onClick={() => handleSendMessage('Cancelar', draft.draft_id ?? undefined)}>Cancelar</button>
              </div>
            </section>
          )}

          {/* Perguntas rápidas */}
          {!!history.data && messages.length === 1 && !draft && (
            <div className="border-t border-slate-200 bg-white px-3 py-3 dark:border-slate-800 dark:bg-slate-950 sm:px-4">
              <p className="mb-2 flex items-center gap-1.5 text-[11px] font-semibold text-slate-600 dark:text-slate-300">
                <WalletCards className="h-3.5 w-3.5" />
                Atalhos úteis
              </p>
              <div className="flex flex-wrap gap-1.5 sm:gap-2">
                {QUICK_QUESTIONS.map((question, index) => (
                  <button
                    key={index}
                    onClick={() => handleSendMessage(question)}
                    className="touch-manipulation rounded-full bg-slate-100 px-3 py-1.5 text-[11px] font-semibold text-slate-700 transition-colors hover:bg-slate-200 active:bg-slate-300 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          )}

          {!draft && !isLoading && !history.isPending && !history.isError && (
            <div className="shrink-0 border-t border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-950 sm:px-4">
              {quickKind ? <QuickEntryForm key={quickKind} kind={quickKind} onCancel={() => setQuickKind(null)} onSubmit={entry => {
                const amount = (entry.amount_cents / 100).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
                const message = (entry.kind === 'expense' ? 'Gasto extra' : 'Receita') + ': ' + entry.name + ' · ' + amount + ' · ' + entry.day.split('-').reverse().join('/')
                setQuickKind(null)
                void submit({ message, request_id: crypto.randomUUID(), draft_id: 'none', entry })
              }} /> : <div className="flex gap-2">
                <button type="button" onClick={() => setQuickKind('expense')} className="min-h-10 rounded-md bg-teal-800 px-3 text-sm font-semibold text-white">+ Gasto extra</button>
                <button type="button" onClick={() => setQuickKind('income')} className="min-h-10 rounded-md border border-slate-300 px-3 text-sm font-semibold">+ Receita</button>
              </div>}
            </div>
          )}
          {/* Input */}
          {!quickKind && <div className="safe-area-bottom border-t border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-950 sm:p-4">
            <p className="mb-2 text-xs text-slate-500 dark:text-slate-400">Enter envia · Shift + Enter adiciona uma linha</p>
            <div className="flex space-x-2">
              <textarea
                ref={inputRef}
                rows={3}
                maxLength={16000}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Digite ou cole uma lista de gastos..."
                className="touch-manipulation min-h-[44px] max-h-48 resize-y flex-1 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-950 focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-white dark:placeholder:text-slate-500"
                disabled={isLoading || history.isPending || history.isError}
                aria-label="Mensagem ao assistente"
                autoComplete="off"
                autoCorrect="off"
                autoCapitalize="off"
                spellCheck="false"
              />
              <button
                onClick={() => handleSendMessage()}
                disabled={!inputText.trim() || isLoading || history.isPending || history.isError}
                className="flex min-w-[44px] items-center justify-center rounded-lg bg-slate-950 px-3 py-2 text-white transition-colors hover:bg-slate-800 active:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50 touch-manipulation sm:px-4"
                aria-label="Enviar mensagem"
              >
                <Send className="w-4 h-4 sm:w-4 sm:h-4" />
              </button>
            </div>
          </div>}
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

