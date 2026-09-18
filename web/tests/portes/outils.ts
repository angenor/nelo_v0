// Ce que les specs Playwright partagent : les écrans déclarés, les adresses, la sonde de réseau.
import type { BrowserContext } from '@playwright/test'
import { existsSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import type { Ecran } from '../../app/core/ecrans'
import { lireEcrans } from '../../app/core/ecrans'

export const ECRANS: Ecran[] = lireEcrans(readFileSync(join(import.meta.dirname, '../../ecrans.json'), 'utf8'))
export const PORT_DEV = Number(process.env.NELO_WEB_PORT_DEV ?? 4311)
/** La racine que le relais sert, sous l'origine de l'application (core/api/client.ts). */
export const RACINE_API = '/api/v1'
export const THEMES = ['light', 'dark'] as const

/** L'état enregistré par le projet « setup » : les cookies d'une session réelle (research.md R-11). */
export const ETAT_SESSION = join(import.meta.dirname, '../../test-results/session.json')

export interface Visite {
  ecran: Ecran
  persona: string | undefined
  /** Vrai quand l'écran se visite avec la session semée, jamais avec un persona. */
  session: boolean
  adresse: string
  nom: string
}

/**
 * Chaque écran déclaré, une fois par persona (ou une fois s'il n'en a pas). Un écran de session
 * se visite avec l'état enregistré, les autres sans : `session` dit lequel.
 */
export function visites(filtre: (e: Ecran) => boolean = () => true): Visite[] {
  return ECRANS.filter(filtre).flatMap((ecran) =>
    (ecran.personas ?? [undefined]).map((persona) => ({
      ecran,
      persona,
      session: ecran.session === true,
      adresse:
        (ecran.developpement ? `http://localhost:${PORT_DEV}` : '') +
        ecran.route +
        (persona ? `?persona=${persona}` : ''),
      nom: persona ? `${ecran.nom} (${persona})` : ecran.nom,
    })),
  )
}

/**
 * Pose les cookies de la session semée sur un contexte de navigateur (research.md R-11). Les
 * jetons sont `HttpOnly` : aucun script ne les lit, seul le navigateur les renvoie, et c'est
 * bien ce que la porte veut vérifier.
 */
export async function ouvrirLaSession(contexte: BrowserContext): Promise<void> {
  if (!existsSync(ETAT_SESSION)) {
    throw new Error(
      `session semée : ${ETAT_SESSION} absent, lancer la porte avec NELO_SESSION_SEMEE=1`,
    )
  }
  const etat = JSON.parse(readFileSync(ETAT_SESSION, 'utf8')) as {
    cookies: Parameters<BrowserContext['addCookies']>[0]
  }
  await contexte.addCookies(etat.cookies)
}

/** Mémorise un thème sur l'appareil avant la navigation : c'est l'application qui le pose. */
export function scriptTheme(theme: string): string {
  return `try { localStorage.setItem('theme', ${JSON.stringify(theme)}) } catch {}`
}
