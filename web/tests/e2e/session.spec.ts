// US5 : ce qui ferme une session, et ce qui ne la ferme pas.
//
// Ce que cette suite prouve dans un navigateur réel :
//   - « Fermer la session » ramène à l'écran de connexion, et l'appareil reste connu ;
//   - un jeton d'accès disparu se renouvelle sans que la personne s'en aperçoive ;
//   - **aucun jeton n'est lisible d'un script** : ni en stockage, ni en cookie de page.
import { existsSync, readFileSync } from 'node:fs'
import { expect, test } from '@playwright/test'
import { uuid7 } from '../../app/core/api/uuid7'
import { ETAT_SESSION } from '../portes/outils'

const JOURNAL = process.env.NELO_SMS_JOURNAL ?? ''
const NUMERO_FERMETURE = process.env.NUMERO_FERMETURE ?? ''
const CODE = /(?<!\d)(\d{6})(?!\d)/

function envoisVers(numero: string): { destinataire: string; texte: string }[] {
  if (!existsSync(JOURNAL)) return []
  return readFileSync(JOURNAL, 'utf8')
    .split('\n')
    .filter((ligne) => ligne.trim() !== '')
    .map((ligne) => JSON.parse(ligne))
    .filter((envoi) => envoi.destinataire === numero)
}

async function attendreCode(numero: string, deja: number): Promise<string> {
  for (let essai = 0; essai < 100; essai++) {
    const vers = envoisVers(numero)
    const trouve = vers.length > deja ? CODE.exec(vers[vers.length - 1]!.texte)?.[1] : undefined
    if (trouve) return trouve
    await new Promise((resoudre) => setTimeout(resoudre, 100))
  }
  throw new Error(`aucun code pour ${numero}`)
}

test.use({ viewport: { width: 390, height: 844 }, storageState: ETAT_SESSION })

test('aucun jeton n’est à portée d’un script', async ({ page, context }) => {
  await page.goto('/')

  const stockage = await page.evaluate(() => {
    const lire = (magasin: Storage) => Object.entries({ ...magasin }).map(([c, v]) => `${c}=${v}`)
    try {
      return [...lire(localStorage), ...lire(sessionStorage), document.cookie].join('\n')
    } catch {
      return ''
    }
  })

  for (const nom of ['nelo_acces', 'nelo_refresh', 'nelo_appareils']) {
    expect(stockage, `${nom} ne doit pas être lisible d’un script`).not.toContain(nom)
  }
  // Un JWT commence par « eyJ » : aucun ne doit traîner dans ce qu'un script peut lire.
  expect(stockage).not.toContain('eyJ')

  const cookies = await context.cookies()
  for (const nom of ['nelo_acces', 'nelo_refresh', 'nelo_appareils']) {
    const cookie = cookies.find((c) => c.name === nom)
    if (cookie) expect(cookie.httpOnly, `${nom} doit être HttpOnly`).toBe(true)
  }
})

test('un jeton d’accès disparu se renouvelle sans que la page change', async ({ page, context }) => {
  await page.goto('/')
  const avant = page.url()

  // Le cookie du jeton d'accès disparaît : c'est ce qui arrive au bout d'une heure.
  await context.clearCookies({ name: 'nelo_acces' })
  await page.reload()

  await expect(page).toHaveURL(avant)
  await expect(page.locator('body')).not.toContainText('AUT_')
})

test('fermer la session ramène à la connexion, et l’appareil reste connu', async ({ browser }) => {
  // Cette suite ferme ce qu'elle ouvre : elle ne touche pas à la session semée, dont les autres
  // suites se servent en parallèle. Son compte lui appartient (NUMERO_FERMETURE).
  expect(NUMERO_FERMETURE, 'NUMERO_FERMETURE n’est pas posé').not.toBe('')
  const contexte = await browser.newContext({ viewport: { width: 390, height: 844 } })
  try {
    const page = await contexte.newPage()
    const deja = envoisVers(NUMERO_FERMETURE).length

    await page.goto('/connexion')
    // L'écran doit être prêt : un clic avant l'hydratation ne déclencherait rien.
    await expect(page.locator('form button[type="submit"]')).toBeEnabled()
    await page.getByRole('textbox').fill(NUMERO_FERMETURE.replace(/^\+225/, ''))
    await page.locator('form button[type="submit"]').click()
    await expect(page).toHaveURL(/\/connexion\/code/)
    await page.getByRole('textbox').fill(await attendreCode(NUMERO_FERMETURE, deja))
    await page.locator('form button[type="submit"]').click()
    await page.waitForURL(/\/connexion\/pin$|localhost:\d+\/$/, { timeout: 15000 })

    const fermeture = await page.request.delete('/api/v1/auth/session', {
      headers: { 'X-Nelo-Requete': uuid7() },
    })
    expect(fermeture.status(), await fermeture.text()).toBe(204)

    await page.goto('/')
    await expect(page).toHaveURL(/\/connexion/, { timeout: 15000 })

    // L'appareil reste connu : la réouverture se fait par code personnel, pas par un SMS de plus.
    const comptes = await page.request.get('/api/v1/auth/appareil')
    expect((await comptes.json()).comptes.length).toBeGreaterThan(0)
  } finally {
    await contexte.close()
  }
})
