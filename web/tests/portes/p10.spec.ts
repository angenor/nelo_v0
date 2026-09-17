// PORTE P-10 : chaque écran budgété tient son plafond, mesuré en octets transférés par le
// protocole du navigateur, service worker bloqué (une première visite) ; deux nombres, l'application
// et les polices (Q29, issue B à titre provisoire) ; aucune ressource hors de l'application ; et le
// premier affichage utile en 3G lente (research.md R-13, R-16).
import type { CDPSession } from '@playwright/test'
import { expect, test } from '@playwright/test'
import { ECRANS, visites } from './outils'

const ko = (octets: number) => (Math.round((octets / 1024) * 10) / 10).toLocaleString('fr-FR')
const HOTES_LOCAUX = new Set(['localhost', '127.0.0.1', '[::1]'])

interface Mesure {
  application: number
  polices: number
  horsApplication: string[]
}

async function mesurer(cdp: CDPSession): Promise<Mesure> {
  const adresses = new Map<string, string>()
  const mesure: Mesure = { application: 0, polices: 0, horsApplication: [] }
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
    if (/\.woff2(\?|$)/.test(url)) mesure.polices += e.encodedDataLength
    else mesure.application += e.encodedDataLength
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
    const cdp = await context.newCDPSession(page)
    const mesure = await mesurer(cdp)
    await page.goto(visite.adresse, { waitUntil: 'networkidle' })
    const { budgetKo, budgetPolicesKo } = visite.ecran
    const total = mesure.application + mesure.polices
    console.log(
      `PORTE P-10 : ${visite.nom} plafond ${budgetKo} Ko mesuré ${ko(mesure.application)} Ko ` +
        `(polices ${ko(mesure.polices)} Ko sur ${budgetPolicesKo ?? '?'}, total ${ko(total)} Ko)`,
    )
    const echec = (motif: string) => `PORTE P-10 ÉCHOUÉE : ${visite.nom} ${motif}`
    expect(mesure.horsApplication, echec(`ressource hors de l’application : ${mesure.horsApplication.join(', ')}`)).toEqual([])
    expect(mesure.application, echec(`plafond ${budgetKo} Ko, mesuré ${ko(mesure.application)} Ko`)).toBeLessThanOrEqual(budgetKo! * 1024)
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
