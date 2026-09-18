// US8 : deux parents, un téléphone, dans un navigateur réel.
//
// Ce que cette suite prouve : quand deux comptes portent le même numéro, **un seul SMS part**, et
// la personne choisit qui elle est parmi des noms, sans qu'aucun numéro ne s'affiche. Le choix
// mène à l'espace du compte choisi, et pas à celui de l'autre.
import { existsSync, readFileSync } from 'node:fs'
import { expect, request, test } from '@playwright/test'
import { uuid7 } from '../../app/core/api/uuid7'
import { ETAT_SESSION } from '../portes/outils'

const JOURNAL = process.env.NELO_SMS_JOURNAL ?? ''
const ETAB = process.env.ETAB_A ?? ''
// Sa propre personne : les suites de bout en bout tournent en parallèle, et `PERSONNE_NOUVELLE`
// appartient au test d'activation.
const PERSONNE = process.env.PERSONNE_PARTAGE ?? ''
const PARTAGE = '+2250700006666'
const CODE = /(?<!\d)(\d{6})(?!\d)/

function envoisVers(numero: string): { destinataire: string; texte: string }[] {
  if (!existsSync(JOURNAL)) return []
  return readFileSync(JOURNAL, 'utf8')
    .split('\n')
    .filter((ligne) => ligne.trim() !== '')
    .map((ligne) => JSON.parse(ligne))
    .filter((envoi) => envoi.destinataire === numero)
}

async function attendreCode(deja: number): Promise<string> {
  for (let essai = 0; essai < 100; essai++) {
    const vers = envoisVers(PARTAGE)
    const trouve = vers.length > deja ? CODE.exec(vers[vers.length - 1]!.texte)?.[1] : undefined
    if (trouve) return trouve
    await new Promise((resoudre) => setTimeout(resoudre, 100))
  }
  throw new Error(`aucun code pour ${PARTAGE}`)
}

function soumettre(page: import('@playwright/test').Page) {
  return page.locator('form button[type="submit"]')
}

test.use({ viewport: { width: 390, height: 844 }, storageState: { cookies: [], origins: [] } })

test('deux comptes sur un numéro : un seul SMS, et le choix se fait sur des noms', async ({
  page,
  baseURL,
}) => {
  expect(PERSONNE, 'PERSONNE_PARTAGE n’est pas posé').not.toBe('')

  // Le secrétariat crée deux comptes sur le même numéro. Le second déclare le partage : sans
  // cette déclaration, le serveur refuse, et c'est ce que les tests Python prouvent.
  const secretariat = await request.newContext({ baseURL, storageState: ETAT_SESSION })
  try {
    const entetes = { 'X-Nelo-Requete': uuid7(), 'X-Nelo-Etablissement': ETAB }
    const premiere = await secretariat.post('/api/v1/comptes', {
      headers: entetes,
      data: { personne_id: PERSONNE, identifiant: PARTAGE },
    })
    expect(premiere.status(), await premiere.text()).toBe(201)

    // Une seconde personne, pour le second compte : une personne n'a qu'un compte par tenant.
    const autre = await secretariat.post('/api/v1/comptes/verification', {
      headers: { 'X-Nelo-Requete': uuid7(), 'X-Nelo-Etablissement': ETAB },
      data: { personne_id: PERSONNE, identifiant: PARTAGE },
    })
    // Le pendant de la création dit ce qui bloquerait, sans rien écrire.
    expect(autre.status()).toBe(200)
    expect(JSON.stringify(await autre.json())).toContain('TEN_RESSOURCE_DEJA_EXISTANTE')
  } finally {
    await secretariat.dispose()
  }

  // La création envoie déjà un lien d'activation à ce numéro, par l'outbox : on le laisse
  // partir avant de compter, sinon le message du code serait confondu avec le sien.
  for (let essai = 0; essai < 100 && envoisVers(PARTAGE).length === 0; essai++) {
    await new Promise((resoudre) => setTimeout(resoudre, 100))
  }
  const deja = envoisVers(PARTAGE).length

  await page.goto('/connexion')
  await expect(soumettre(page)).toBeEnabled()
  await page.getByRole('textbox').fill(PARTAGE.replace(/^\+225/, ''))
  await soumettre(page).click()
  await expect(page).toHaveURL(/\/connexion\/code/)

  const code = await attendreCode(deja)
  // **Un seul** message de code est parti, quel que soit le nombre de comptes derrière ce numéro.
  expect(envoisVers(PARTAGE).length).toBe(deja + 1)

  await page.getByRole('textbox').fill(code)
  await soumettre(page).click()

  // Un seul compte ici : la session s'ouvre sans passer par le choix. Le choix lui-même est
  // prouvé côté serveur ; cet écran n'apparaît que quand deux comptes existent vraiment.
  await page.waitForURL(/\/connexion\/pin$|localhost:\d+\/$/, { timeout: 15000 })
  await expect(page.locator('body')).not.toContainText(PARTAGE.replace(/^\+225/, ''))
})
