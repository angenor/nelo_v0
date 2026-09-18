// US3 : le code personnel, dans un navigateur réel.
//
// Ce que cette suite prouve : quatre chiffres définis remplacent le SMS à l'ouverture suivante,
// **sans qu'aucun message ne parte** et sans qu'aucun numéro n'apparaisse à l'écran ; sur un
// navigateur qui n'a jamais ouvert de session, le code personnel n'est pas même proposé.
//
// La session semée définit déjà son code personnel (tests/session.setup.ts) : cette suite en
// ouvre une autre, avec son propre numéro, pour ne rien lui prendre.
import { existsSync, readFileSync } from 'node:fs'
import { expect, test } from '@playwright/test'
import { uuid7 } from '../../app/core/api/uuid7'

const JOURNAL = process.env.NELO_SMS_JOURNAL ?? ''
const NUMERO = process.env.NUMERO_FICTIF ?? ''
const CODE = /(?<!\d)(\d{6})(?!\d)/
const PIN = '2580'

function lignes(): { destinataire: string; texte: string }[] {
  if (!existsSync(JOURNAL)) return []
  return readFileSync(JOURNAL, 'utf8')
    .split('\n')
    .filter((ligne) => ligne.trim() !== '')
    .map((ligne) => JSON.parse(ligne))
}

async function attendreCode(numero: string, deja: number): Promise<string> {
  for (let essai = 0; essai < 100; essai++) {
    const vers = lignes().filter((e) => e.destinataire === numero)
    const trouve = vers.length > deja ? CODE.exec(vers[vers.length - 1]!.texte)?.[1] : undefined
    if (trouve) return trouve
    await new Promise((resoudre) => setTimeout(resoudre, 100))
  }
  throw new Error(`aucun code pour ${numero}`)
}

function soumettre(page: import('@playwright/test').Page) {
  return page.locator('form button[type="submit"]')
}

test.use({ viewport: { width: 390, height: 844 }, storageState: { cookies: [], origins: [] } })

test('définir un code personnel, puis rouvrir sans le moindre SMS', async ({ page }) => {
  expect(NUMERO, 'NUMERO_FICTIF n’est pas posé').not.toBe('')
  const deja = lignes().filter((e) => e.destinataire === NUMERO).length

  // Ouvrir par code reçu, puis définir le code personnel.
  await page.goto('/connexion')
  await page.getByRole('textbox').fill(NUMERO.replace(/^\+225/, ''))
  await soumettre(page).click()
  await expect(page).toHaveURL(/\/connexion\/code/)
  await page.getByRole('textbox').fill(await attendreCode(NUMERO, deja))
  await soumettre(page).click()
  await page.waitForURL(/\/connexion\/pin$/, { timeout: 15000 })

  const champs = page.getByRole('textbox')
  await champs.nth(0).fill(PIN)
  await champs.nth(1).fill(PIN)
  await soumettre(page).click()
  await page.waitForURL(/localhost:\d+\/$/, { timeout: 15000 })

  // Fermer la session : l'appareil, lui, reste connu.
  await page.request.delete('/api/v1/auth/session', { headers: { 'X-Nelo-Requete': uuid7() } })
  const messagesAvant = lignes().length

  await page.goto('/connexion')
  // L'écran propose un nom, et **jamais** un numéro.
  await expect(page.getByText(NUMERO.replace(/^\+225/, ''))).toHaveCount(0)
  await page.getByRole('textbox').first().fill(PIN)
  await soumettre(page).click()

  await page.waitForURL(/localhost:\d+\/$/, { timeout: 15000 })
  expect(lignes().length, 'aucun message ne doit partir pour une ouverture par code personnel').toBe(
    messagesAvant,
  )
})

test('sur un navigateur qui n’a jamais ouvert de session, le code personnel n’est pas proposé', async ({
  page,
}) => {
  await page.goto('/connexion')

  // Rien à deviner : l'écran demande un numéro, comme la première fois.
  await expect(page.getByRole('textbox')).toHaveCount(1)
  const texte = (await page.locator('body').innerText()).toLowerCase()
  expect(texte).toContain('sms')
})
