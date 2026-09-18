// PORTE P-10 : chaque écran budgété tient son plafond, mesuré en octets transférés par le
// protocole du navigateur, service worker bloqué (une première visite) ; deux nombres, l'application
// et les polices (Q29, issue B à titre provisoire) ; aucune ressource hors de l'application ; et le
// premier affichage utile en 3G lente (research.md R-13, R-16).
import { readdirSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import type { CDPSession } from '@playwright/test'
import { expect, test } from '@playwright/test'
import { ECRANS, ouvrirLaSession, visites } from './outils'

const ko = (octets: number) => (Math.round((octets / 1024) * 10) / 10).toLocaleString('fr-FR')
const HOTES_LOCAUX = new Set(['localhost', '127.0.0.1', '[::1]'])

interface Mesure {
  application: number
  polices: number
  horsApplication: string[]
  /**
   * Ce que la démonstration pèse dans cette visite. Une adresse `?persona=` charge les personas
   * et leurs données ; la constante `__NELO_DEMONSTRATION__` vaut `false` en production et
   * l'empaqueteur les élague (research.md R-10), donc ces octets ne voyagent jamais chez une
   * personne : ils ne comptent pas dans le plafond. La visite de l'accueil réel, elle, vérifie
   * qu'aucun n'y paraît (research.md R-22), et c'est cette mesure qui fait foi.
   */
  demonstration: number
  demonstrationVues: string[]
}

const DEMONSTRATION = join(import.meta.dirname, '../../app/core/demonstration')
const SOURCE_DEMONSTRATION = join(import.meta.dirname, '../../app/core/contexte/demonstration.ts')
const PRECOMPUTE = join(import.meta.dirname, '../../.output/server/chunks/virtual/precomputed.mjs')

/** Les modules du dossier de démonstration, sans leur extension. */
function modulesDeDemonstration(): Set<string> {
  return new Set(readdirSync(DEMONSTRATION).map((f) => f.replace(/\.[a-z]+$/, '')))
}

/**
 * Ceux que la **source** de démonstration charge, et eux seuls : les imports dynamiques de
 * `core/contexte/demonstration.ts`, lus dans le fichier plutôt qu'écrits ici. C'est cette
 * branche que `__NELO_DEMONSTRATION__` gouverne et que la production élague (research.md R-10).
 */
function modulesDeLaSource(): Set<string> {
  const source = readFileSync(SOURCE_DEMONSTRATION, 'utf8')
  const noms = new Set<string>()
  for (const m of source.matchAll(/import\(['"`][^'"`]*demonstration\/([\w.-]+)['"`]\)/g)) {
    noms.add(m[1]!.replace(/\.[a-z]+$/, ''))
  }
  return noms
}

/**
 * Les fichiers empaquetés d'un jeu de modules. Les morceaux servis portent une empreinte
 * (`CPdT4iug.js`) : seul le registre de la construction dit de quel module ils viennent.
 */
function fichiersDe(modules: Set<string>): Set<string> {
  const registre = readFileSync(PRECOMPUTE, 'utf8')
  const fichiers = new Set<string>()
  for (const m of registre.matchAll(/file:"([^"]+)",name:"([^"]+)"/g)) {
    if (modules.has(m[2]!)) fichiers.add(m[1]!)
  }
  return fichiers
}

/** Tout ce qui vient du dossier de démonstration : ces octets ne sont pas ceux du produit. */
const FICHIERS_DEMONSTRATION = fichiersDe(modulesDeDemonstration())
/**
 * Ce que la source de démonstration charge. Sur une visite sans persona, **rien** de cela ne
 * doit paraître : c'est la preuve de l'élagage que R-22 demande à l'accueil réel.
 *
 * Les données de démonstration des écrans de T0b (`donnees`, `pack-demonstration`) sont, elles,
 * importées d'office par trois pages : elles voyagent encore, et c'est T1b qui les remplace par
 * les vraies. Elles ne comptent pas dans le plafond, mais la porte ne prétend pas qu'elles ont
 * disparu.
 */
const FICHIERS_SOURCE = fichiersDe(modulesDeLaSource())

function nomDeFichier(url: string): string {
  return url.split('?')[0]!.split('/').pop() ?? ''
}

async function mesurer(cdp: CDPSession): Promise<Mesure> {
  const adresses = new Map<string, string>()
  const mesure: Mesure = {
    application: 0,
    polices: 0,
    horsApplication: [],
    demonstration: 0,
    demonstrationVues: [],
  }
  await cdp.send('Network.enable')
  await cdp.send('Network.setCacheDisabled', { cacheDisabled: true })
  cdp.on('Network.requestWillBeSent', (e) => {
    adresses.set(e.requestId, e.request.url)
    const url = new URL(e.request.url)
    if (url.protocol.startsWith('http') && !HOTES_LOCAUX.has(url.hostname)) mesure.horsApplication.push(e.request.url)
    if (e.redirectResponse) mesure.application += e.redirectResponse.encodedDataLength ?? 0
  })
  cdp.on('Network.loadingFinished', (e) => {
    const url = adresses.get(e.requestId) ?? ''
    if (/\.woff2(\?|$)/.test(url)) {
      mesure.polices += e.encodedDataLength
      return
    }
    mesure.application += e.encodedDataLength
    const fichier = nomDeFichier(url)
    if (FICHIERS_DEMONSTRATION.has(fichier)) mesure.demonstration += e.encodedDataLength
    if (FICHIERS_SOURCE.has(fichier)) mesure.demonstrationVues.push(url)
  })
  return mesure
}

test('P-10 : les écrans sans budget sont listés', () => {
  const sansBudget = ECRANS.filter((e) => e.budgetKo === null && !e.developpement).map((e) => e.nom)
  console.log(`PORTE P-10 : non budgété : ${sansBudget.length ? sansBudget.join(', ') : 'aucun'}`)
  const nonMesures = ECRANS.filter((e) => e.budgetKo === null && e.developpement).map((e) => e.nom)
  console.log(`PORTE P-10 : écrans de développement, jamais construits : ${nonMesures.join(', ')}`)
})

for (const visite of visites((e) => e.budgetKo !== null && !e.developpement)) {
  test(`P-10 : ${visite.nom}`, async ({ page, context }) => {
    // Un écran de session se visite avec l'état enregistré, jamais avec un persona.
    if (visite.session) await ouvrirLaSession(context)
    const cdp = await context.newCDPSession(page)
    const mesure = await mesurer(cdp)
    await page.goto(visite.adresse, { waitUntil: 'networkidle' })
    const { budgetKo, budgetPolicesKo } = visite.ecran
    const produit = mesure.application - mesure.demonstration
    const total = mesure.application + mesure.polices
    console.log(
      `PORTE P-10 : ${visite.nom} plafond ${budgetKo} Ko mesuré ${ko(produit)} Ko ` +
        `(polices ${ko(mesure.polices)} Ko sur ${budgetPolicesKo ?? '?'}, ` +
        `démonstration ${ko(mesure.demonstration)} Ko, total ${ko(total)} Ko)`,
    )
    const echec = (motif: string) => `PORTE P-10 ÉCHOUÉE : ${visite.nom} ${motif}`
    expect(mesure.horsApplication, echec(`ressource hors de l’application : ${mesure.horsApplication.join(', ')}`)).toEqual([])
    // L'accueil réel n'emporte aucun morceau de la démonstration : la branche est morte en
    // production, et sur une session semée l'adresse ne porte aucun persona (research.md R-10).
    if (visite.session) {
      expect(
        mesure.demonstrationVues,
        echec(`ressource de démonstration : ${mesure.demonstrationVues.join(', ')}`),
      ).toEqual([])
    }
    expect(produit, echec(`plafond ${budgetKo} Ko, mesuré ${ko(produit)} Ko`)).toBeLessThanOrEqual(budgetKo! * 1024)
    if (budgetPolicesKo) {
      expect(mesure.polices, echec(`polices : plafond ${budgetPolicesKo} Ko, mesuré ${ko(mesure.polices)} Ko`)).toBeLessThanOrEqual(budgetPolicesKo * 1024)
    }
  })
}

test('P-10 : premier affichage utile en 3G lente, sous deux secondes', async ({ page, context }) => {
  const cdp = await context.newCDPSession(page)
  await cdp.send('Network.enable')
  await cdp.send('Network.setCacheDisabled', { cacheDisabled: true })
  await cdp.send('Network.emulateNetworkConditions', {
    offline: false,
    latency: 400,
    downloadThroughput: (400 * 1000) / 8,
    uploadThroughput: (400 * 1000) / 8,
  })
  const debut = Date.now()
  await page.goto('/d/vie_scolaire?persona=un-domaine', { waitUntil: 'commit' })
  await page.getByRole('status', { name: 'État de la saisie' }).waitFor({ state: 'visible', timeout: 10_000 })
  const duree = Date.now() - debut
  console.log(`PORTE P-10 : premier affichage utile en 3G lente ${duree} ms (ruban visible), plafond 2000 ms`)
  expect(duree, `PORTE P-10 ÉCHOUÉE : premier affichage utile ${duree} ms, plafond 2000 ms`).toBeLessThanOrEqual(2000)
})
