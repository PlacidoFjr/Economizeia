import { BarChart3, Bot, CalendarDays, ShieldCheck } from 'lucide-react'

const ITEMS = [
  { icon: Bot, label: 'Chat econômico' },
  { icon: CalendarDays, label: 'Histórico mensal' },
  { icon: BarChart3, label: 'Painel financeiro' },
  { icon: ShieldCheck, label: 'Dados protegidos' },
]

export default function AuthVisualPanel() {
  return (
    <aside className="relative hidden min-h-[560px] overflow-hidden lg:block">
      <div
        className="absolute inset-0 bg-cover bg-center"
        style={{
          backgroundImage:
            "url('https://images.pexels.com/photos/35028998/pexels-photo-35028998.jpeg?auto=compress&cs=tinysrgb&w=1260&h=900&dpr=1')",
        }}
      />
      <div className="absolute inset-0 bg-slate-950/66" />
      <div className="absolute inset-0 bg-gradient-to-br from-slate-950/92 via-slate-950/58 to-slate-950/82" />
      <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-slate-950 via-slate-950/78 to-transparent" />

      <div className="relative z-10 flex h-full min-h-[560px] flex-col justify-between p-8 text-white xl:p-10">
        <div className="text-2xl font-bold">
          Economize<span className="text-cyan-300">IA</span>
        </div>

        <div />

        <div className="grid grid-cols-2 gap-3">
          {ITEMS.map((item) => {
            const Icon = item.icon
            return (
              <div key={item.label} className="rounded-lg border border-white/15 bg-slate-950/58 p-3 shadow-lg shadow-slate-950/25 backdrop-blur-md xl:p-4">
                <Icon className="mb-2 h-5 w-5 text-cyan-300 xl:mb-3" />
                <p className="text-sm font-semibold text-white">{item.label}</p>
              </div>
            )
          })}
        </div>
      </div>
    </aside>
  )
}
