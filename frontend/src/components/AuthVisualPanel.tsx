import { BarChart3, Bot, CalendarDays, ShieldCheck } from 'lucide-react'

const ITEMS = [
  { icon: Bot, label: 'Chat econômico' },
  { icon: CalendarDays, label: 'Histórico mensal' },
  { icon: BarChart3, label: 'Painel financeiro' },
  { icon: ShieldCheck, label: 'Dados protegidos' },
]

export default function AuthVisualPanel() {
  return (
    <aside className="relative hidden min-h-screen overflow-hidden lg:block">
      <div
        className="absolute inset-0 scale-[1.02] bg-cover bg-center"
        style={{
          backgroundImage:
            "url('https://images.pexels.com/photos/35028998/pexels-photo-35028998.jpeg?auto=compress&cs=tinysrgb&w=1260&h=900&dpr=1')",
        }}
      />
      <div className="absolute inset-0 bg-slate-950/52" />
      <div className="absolute inset-0 bg-gradient-to-br from-slate-950/78 via-slate-950/36 to-slate-950/78" />
      <div className="absolute inset-x-0 bottom-0 h-2/3 bg-gradient-to-t from-slate-950 via-slate-950/70 to-transparent" />

      <div className="relative z-10 flex h-full min-h-screen flex-col items-center justify-between p-8 text-white xl:p-12">
        <div className="self-start text-2xl font-bold tracking-tight notranslate" translate="no">
          Economize<span className="text-cyan-300">IA</span>
        </div>

        <div className="w-full max-w-sm text-center">
          <div className="mx-auto h-px w-16 bg-cyan-300/70" />
        </div>

        <div className="grid w-full max-w-md grid-cols-2 gap-3">
          {ITEMS.map((item) => {
            const Icon = item.icon
            return (
              <div key={item.label} className="rounded-lg border border-white/15 bg-slate-950/50 p-4 shadow-lg shadow-slate-950/25 backdrop-blur-md">
                <Icon className="mb-3 h-5 w-5 text-cyan-300" />
                <p className="text-sm font-semibold text-white">{item.label}</p>
              </div>
            )
          })}
        </div>
      </div>
    </aside>
  )
}
