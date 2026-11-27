import { useEffect, useRef, useState } from 'react'
import { Download, X } from 'lucide-react'
import { getInstallPrompt, isStandalone, promptInstallation } from '../services/pwa'

export default function InstallApp() {
  const [installed, setInstalled] = useState(isStandalone)
  const [open, setOpen] = useState(false)
  const [error, setError] = useState('')
  const dialog = useRef<HTMLDialogElement>(null)
  const trigger = useRef<HTMLButtonElement>(null)
  const ios = /iphone|ipad|ipod/i.test(navigator.userAgent) ||
    (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)

  useEffect(() => {
    const update = () => setInstalled(isStandalone())
    const installed = () => { setInstalled(true); setOpen(false) }
    const display = window.matchMedia('(display-mode: standalone)')
    window.addEventListener('pwa-install-change', update)
    window.addEventListener('appinstalled', installed)
    display.addEventListener('change', update)
    return () => {
      window.removeEventListener('pwa-install-change', update)
      window.removeEventListener('appinstalled', installed)
      display.removeEventListener('change', update)
    }
  }, [])
  useEffect(() => {
    if (open) dialog.current?.showModal()
    else dialog.current?.close()
  }, [open])
  if (installed) return null
  return <>
    <button ref={trigger} type="button" aria-label="Instalar app" title="Instalar EconomizeIA"
      className="inline-flex min-h-11 items-center gap-2 rounded-md border border-slate-200 px-3 text-sm font-semibold text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-900"
      onClick={async () => {
        if (getInstallPrompt()) {
          try { await promptInstallation(); return } catch { setError('Use o menu do navegador para instalar o app.') }
        }
        setOpen(true)
      }}>
      <Download size={18} aria-hidden="true" /><span className="hidden xl:inline">Instalar app</span>
    </button>
    <dialog ref={dialog} onCancel={() => setOpen(false)} onClose={() => { setOpen(false); trigger.current?.focus() }}
      aria-labelledby="install-title" className="w-[calc(100%_-_2rem)] max-w-md rounded-xl border border-slate-200 bg-white p-5 text-slate-950 shadow-xl backdrop:bg-slate-950/60 dark:border-slate-700 dark:bg-slate-900">
      <div className="flex items-start justify-between gap-3">
        <h2 id="install-title" className="text-lg font-bold">Instalar EconomizeIA</h2>
        <button type="button" aria-label="Fechar instruções de instalação" onClick={() => setOpen(false)} className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md hover:bg-slate-100 dark:hover:bg-slate-800"><X size={20} /></button>
      </div>
      {ios ? <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm">
        <li>Abra este site no Safari.</li>
        <li>Toque em Compartilhar e escolha Adicionar à Tela de Início.</li>
        <li>Ative Abrir como App da Web, se aparecer, e toque em Adicionar.</li>
      </ol> : <p className="mt-3 text-sm leading-6">Abra o menu do navegador e escolha Instalar app ou Adicionar à Tela de Início. No computador, procure também o ícone de instalação na barra de endereço.</p>}
      <p className="mt-3 text-sm text-slate-500">Ao abrir pelo ícone, entre na sua conta para acessar suas finanças. A consulta e o registro de lançamentos usam internet.</p>
      {error && <p role="alert" className="mt-2 text-sm text-amber-700">{error}</p>}
      <button type="button" onClick={() => setOpen(false)} className="mt-4 min-h-11 rounded-lg bg-teal-800 px-4 text-sm font-semibold text-white">Entendi</button>
    </dialog>
  </>
}

