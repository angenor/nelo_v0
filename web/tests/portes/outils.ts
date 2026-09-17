// Ce que les specs Playwright partagent : les écrans déclarés, les adresses, la sonde de réseau.
import brut from '../../ecrans.json'
import type { Ecran } from '../../app/core/ecrans'
import { valider } from '../../app/core/ecrans'

export const ECRANS: Ecran[] = valider(brut.ecrans)
export const PORT_DEV = Number(process.env.NELO_WEB_PORT_DEV ?? 4311)
export const THEMES = ['light', 'dark'] as const

/** Chaque écran déclaré, une fois par persona (ou une fois s'il n'en a pas). */
export function visites(filtre: (e: Ecran) => boolean = () => true) {
  return ECRANS.filter(filtre).flatMap((ecran) =>
    (ecran.personas ?? [undefined]).map((persona) => ({
      ecran,
      persona,
      adresse:
        (ecran.developpement ? `http://localhost:${PORT_DEV}` : '') +
        ecran.route +
        (persona ? `?persona=${persona}` : ''),
      nom: persona ? `${ecran.nom} (${persona})` : ecran.nom,
    })),
  )
}

/** Mémorise un thème sur l'appareil avant la navigation : c'est l'application qui le pose. */
export function scriptTheme(theme: string): string {
  return `try { localStorage.setItem('theme', ${JSON.stringify(theme)}) } catch {}`
}
