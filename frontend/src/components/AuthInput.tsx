import { useState } from 'react'
import type { InputHTMLAttributes, ReactNode } from 'react'

interface AuthInputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  icon?: ReactNode
}

export default function AuthInput({ label, icon, className = '', ...props }: AuthInputProps) {
  const [mouseX, setMouseX] = useState(0)
  const [isHovering, setIsHovering] = useState(false)

  return (
    <div className="w-full">
      <label htmlFor={props.id} className="mb-2 block text-sm font-semibold text-slate-700 dark:text-slate-300">
        {label}
      </label>
      <div
        className="relative"
        onMouseMove={(event) => {
          const rect = event.currentTarget.getBoundingClientRect()
          setMouseX(event.clientX - rect.left)
        }}
        onMouseEnter={() => setIsHovering(true)}
        onMouseLeave={() => setIsHovering(false)}
      >
        <input
          {...props}
          className={`relative z-10 block w-full rounded-lg border border-slate-300 bg-white px-4 py-3 text-base text-slate-950 placeholder-slate-400 shadow-sm transition-colors focus:border-slate-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-slate-300 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:border-slate-500 dark:focus:bg-slate-950 dark:focus:ring-slate-700 ${icon ? 'pl-12' : ''} ${className}`}
        />
        {icon && <div className="pointer-events-none absolute left-4 top-1/2 z-20 -translate-y-1/2 text-slate-400">{icon}</div>}
        {isHovering && (
          <>
            <div
              className="pointer-events-none absolute inset-x-0 top-0 z-20 h-px overflow-hidden rounded-t-lg"
              style={{
                background: `radial-gradient(48px circle at ${mouseX}px 0px, rgb(8 145 178), transparent 70%)`,
              }}
            />
            <div
              className="pointer-events-none absolute inset-x-0 bottom-0 z-20 h-px overflow-hidden rounded-b-lg"
              style={{
                background: `radial-gradient(48px circle at ${mouseX}px 1px, rgb(8 145 178), transparent 70%)`,
              }}
            />
          </>
        )}
      </div>
    </div>
  )
}
