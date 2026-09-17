// Le thème choisi sur l'appareil (research.md R-21). « systeme » : aucun attribut, la préférence
// de l'appareil décide ; sinon data-theme sur <html>. Seule valeur que le stockage porte.
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

export function attributTheme(theme: Theme): 'light' | 'dark' | undefined {
  return theme === 'systeme' ? undefined : theme
}
