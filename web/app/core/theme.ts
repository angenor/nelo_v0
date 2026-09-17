// Le thème choisi sur l'appareil (research.md R-21). « systeme » suit la préférence de
// l'appareil ; theme.css ne lisant que [data-theme], l'attribut est toujours posé côté client
// (écart E-13). Le rendu serveur n'en pose aucun. Seule valeur que le stockage porte.
import type { Stockage } from './plateforme/plateforme'

export const THEMES = ['systeme', 'light', 'dark'] as const
export type Theme = (typeof THEMES)[number]

const CLE = 'theme'

export function lireTheme(stockage: Stockage): Theme {
  const valeur = stockage.lire(CLE)
  return valeur === 'light' || valeur === 'dark' ? valeur : 'systeme'
}

export function ecrireTheme(stockage: Stockage, theme: Theme): void {
  if (theme === 'systeme') stockage.effacer(CLE)
  else stockage.ecrire(CLE, theme)
}

export function attributTheme(theme: Theme, appareilSombre: boolean): 'light' | 'dark' {
  if (theme !== 'systeme') return theme
  return appareilSombre ? 'dark' : 'light'
}
