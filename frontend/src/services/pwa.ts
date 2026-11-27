export interface InstallPrompt extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

let pending: InstallPrompt | null = null
const changed = () => window.dispatchEvent(new Event('pwa-install-change'))

export function isStandalone() {
  return window.matchMedia('(display-mode: standalone)').matches ||
    (navigator as Navigator & { standalone?: boolean }).standalone === true
}

export function getInstallPrompt() { return pending }

export function startPwa() {
  window.addEventListener('beforeinstallprompt', event => {
    event.preventDefault()
    pending = event as InstallPrompt
    changed()
  })
  window.addEventListener('appinstalled', () => {
    pending = null
    changed()
  })
  if (import.meta.env.PROD && 'serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      void navigator.serviceWorker.register('/sw.js', { updateViaCache: 'none' }).catch(() => {
        // The online application continues to work when installation is unavailable.
      })
    }, { once: true })
  }
}

export async function promptInstallation() {
  const prompt = pending
  if (!prompt) return false
  pending = null
  changed()
  await prompt.prompt()
  await prompt.userChoice
  return true
}

