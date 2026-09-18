// US1 : le parcours réel, dans un navigateur réel, contre l'API de test et sa base semée.
//
// Ce que cette suite prouve, et que les tests Python ne peuvent pas prouver seuls :
//   - une personne entre son numéro, reçoit un SMS, saisit le code, et entre dans l'application ;
//   - un numéro que personne ne porte mène au **même** écran de code, sans qu'aucun mot ne dise
//     qu'il est inconnu, et sans qu'aucun message ne parte ;
//   - pendant le compte à rebours, le renvoi est absent de l'écran, jamais grisé.
//
// Le code se lit là où une personne le lirait : dans le message, ici le journal de la passerelle
// simulée (NELO_SMS_JOURNAL, posé par scripts/avec-serveur-dev.sh).
import { existsSync, readFileSync } from 'node:fs'
import { expect, test } from '@playwright/test'

const JOURNAL = process.env.NELO_SMS_JOURNAL ?? ''
const NUMERO = process.env.NUMERO_A ?? ''
// Le parcours complet prend le numéro du second tenant : le premier sert à la session semée, et
// deux demandes sur un même numéro dans la minute se refusent, comme en production.
const NUMERO_PARCOURS = process.env.NUMERO_B ?? ''
// Un numéro bien formé que le jeu d'essai ne sème à personne.
const INCONNU = '+2250700009999'
const CODE = /(?<!\d)(\d{6})(?!\d)/
const INDICATIF = /^\+225/

interface EnvoiJournalise {
  destinataire: string
  texte: string
}

function envoisVers(numero: string): EnvoiJournalise[] {
  if (!existsSync(JOURNAL)) return []
  return readFileSync(JOURNAL, 'utf8')
    .split('\n')
    .filter((ligne) => ligne.trim() !== '')
    .map((ligne) => JSON.parse(ligne) as EnvoiJournalise)
    .filter((envoi) => envoi.destinataire === numero)
}

async function attendreCode(numero: string, deja: number): Promise<string> {
  for (let essai = 0; essai < 100; essai++) {
    const envois = envoisVers(numero)
    const trouve = envois.length > deja ? CODE.exec(envois[envois.length - 1]!.texte)?.[1] : undefined
    if (trouve) return trouve
    await new Promise((resoudre) => setTimeout(resoudre, 100))
  }
  throw new Error(`aucun code pour ${numero} dans ${JOURNAL}`)
}

/** Le numéro local, tel qu'une personne le tape : sans son indicatif, que l'écran propose. */
function local(numero: string): string {
  return numero.replace(INDICATIF, '')
}

/** Le bouton principal du formulaire : son libellé change selon l'étape, sa place non. */
function soumettre(page: import('@playwright/test').Page) {
  return page.locator('form button[type="submit"]')
}

test.use({ viewport: { width: 390, height: 844 }, storageState: { cookies: [], origins: [] } })

test('le parcours entier : un numéro, un SMS, un code, la session', async ({ page }) => {
  expect(JOURNAL, 'NELO_SMS_JOURNAL n’est pas posé').not.toBe('')
  expect(NUMERO_PARCOURS, 'NUMERO_B n’est pas posé').not.toBe('')
  const avant = envoisVers(NUMERO_PARCOURS).length

  await page.goto('/connexion')
  await page.getByRole('textbox').fill(local(NUMERO_PARCOURS))
  await soumettre(page).click()
  await expect(page).toHaveURL(/\/connexion\/code/)

  const code = await attendreCode(NUMERO_PARCOURS, avant)
  await page.getByRole('textbox').fill(code)
  const [verification] = await Promise.all([
    page.waitForResponse((reponse) => reponse.url().includes('/auth/otp/verification')),
    soumettre(page).click(),
  ])
  expect(verification.status(), 'la vérification du code').toBe(200)

  // L'écran suivant appartient à la session : le code personnel quand il reste à définir,
  // l'accueil sinon. La navigation est un vrai chargement, parce que les jetons vivent dans des
  // cookies qu'aucun script ne lit et que c'est le serveur qui va chercher le contexte.
  await page.waitForURL(/\/connexion\/pin$|localhost:\d+\/$/, { timeout: 15000 })
  await expect(page.locator('body')).not.toContainText('inconnu')
})

test('un numéro que personne ne porte mène au même écran, et ne dit jamais « inconnu »', async ({
  page,
}) => {
  const avant = envoisVers(INCONNU).length

  await page.goto('/connexion')
  await page.getByRole('textbox').fill(local(INCONNU))
  await soumettre(page).click()

  await expect(page).toHaveURL(/\/connexion\/code/)
  const texte = (await page.locator('body').innerText()).toLowerCase()
  expect(texte).not.toContain('inconnu')
  expect(texte).not.toContain('aucun compte')
  // Et aucun message n'est parti : la réponse est la même, le message non.
  await new Promise((resoudre) => setTimeout(resoudre, 1500))
  expect(envoisVers(INCONNU).length).toBe(avant)
})

test('pendant le compte à rebours, le renvoi est absent et le délai est annoncé', async ({
  page,
}) => {
  await page.goto('/connexion')
  await page.getByRole('textbox').fill(local(NUMERO))
  await soumettre(page).click()
  await expect(page).toHaveURL(/\/connexion\/code/)

  // Une action indisponible est **absente** de l'écran, jamais grisée : rien à cliquer en vain.
  await expect(page.getByRole('button', { name: /renvoyer/i })).toHaveCount(0)
  await expect(page.locator('[data-niveau="attente"]')).toBeVisible()
})
