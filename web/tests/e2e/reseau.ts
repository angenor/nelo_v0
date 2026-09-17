// La sonde de réseau des tests : un navigator.connection simulé, que les tests pilotent. C'est le
// navigateur que l'on pilote, jamais l'application (écart E-09).
import type { BrowserContext, Page } from '@playwright/test'

export const SONDE_RESEAU = `
  (() => {
    const connexion = new EventTarget()
    connexion.effectiveType = '4g'
    Object.defineProperty(Navigator.prototype, 'connection', { get: () => connexion, configurable: true })
    window.__sondeReseau = (type) => {
      connexion.effectiveType = type
      connexion.dispatchEvent(new Event('change'))
    }
  })()
`

export async function reseau(page: Page, contexte: BrowserContext, etat: 'bon' | 'faible' | 'absent') {
  if (etat === 'absent') {
    await contexte.setOffline(true)
    return
  }
  await page.evaluate((type) => (window as unknown as { __sondeReseau(t: string): void }).__sondeReseau(type), etat === 'faible' ? '2g' : '4g')
  await contexte.setOffline(false)
}
