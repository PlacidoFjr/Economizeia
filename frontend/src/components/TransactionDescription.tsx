import { useId, useRef, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../services/api'

export default function TransactionDescription({ id, name, notes }: { id: string; name: string; notes?: string | null }) {
  const dialog = useRef<HTMLDialogElement>(null)
  const titleId = useId()
  const fieldId = useId()
  const [value, setValue] = useState('')
  const client = useQueryClient()
  const save = useMutation({
    mutationFn: () => api.put('/bills/' + id + '/description', { notes: value.trim() || null }),
    onSuccess: async () => {
      await Promise.all(['finances', 'bills', 'bill', 'financial-overview'].map(key => client.invalidateQueries({ queryKey: [key] })))
      dialog.current?.close()
    },
  })
  return <div className="mt-1 min-w-0 whitespace-normal text-sm">
    {notes && <p className="max-w-md whitespace-pre-wrap break-words text-slate-600 dark:text-slate-300">{notes}</p>}
    <button type="button" aria-label={(notes ? 'Editar descrição de ' : 'Adicionar descrição a ') + name}
      className="mt-1 min-h-9 text-left text-xs font-semibold text-teal-800 underline underline-offset-2 dark:text-teal-200"
      onClick={() => { setValue(notes || ''); save.reset(); dialog.current?.showModal() }}>
      {notes ? 'Editar descrição' : 'Adicionar descrição'}
    </button>
    <dialog ref={dialog} aria-labelledby={titleId} onCancel={event => { if (save.isPending) event.preventDefault() }}
      className="m-auto max-h-[85dvh] w-[calc(100%-2rem)] max-w-lg overflow-y-auto rounded-xl border border-slate-200 bg-white p-5 text-slate-900 shadow-xl backdrop:bg-slate-950/60 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100">
      <form onSubmit={event => { event.preventDefault(); save.mutate() }} className="space-y-4">
        <div><h2 id={titleId} className="text-lg font-bold">Descrição do lançamento</h2><p className="mt-1 break-words text-sm text-slate-500">{name}</p></div>
        <div>
          <label htmlFor={fieldId} className="block font-medium">O que você quer lembrar?</label>
          <textarea id={fieldId} autoFocus rows={5} maxLength={2000} value={value} disabled={save.isPending}
            onChange={event => setValue(event.target.value)} placeholder="Ex. café, pão e produtos de limpeza para casa"
            className="mt-2 block w-full rounded-md border border-slate-300 bg-white p-3 text-sm dark:border-slate-600 dark:bg-slate-950" />
          <p className="mt-1 text-xs text-slate-500">Opcional · até 2.000 caracteres</p>
        </div>
        {save.isError && <p role="alert" className="text-sm text-red-700 dark:text-red-300">Não foi possível salvar a descrição. Tente novamente.</p>}
        <div className="flex flex-wrap justify-end gap-2">
          <button type="button" disabled={save.isPending} onClick={() => dialog.current?.close()} className="min-h-10 rounded-md border border-slate-300 px-4 text-sm">Cancelar</button>
          <button disabled={save.isPending} className="min-h-10 rounded-md bg-teal-800 px-4 text-sm font-semibold text-white disabled:opacity-50">{save.isPending ? 'Salvando...' : 'Salvar descrição'}</button>
        </div>
      </form>
    </dialog>
  </div>
}
