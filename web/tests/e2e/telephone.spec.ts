// US7 : changer de numéro en libre-service, dans un navigateur réel.
//
// Ce que cette suite prouve : le code part vers le **nouveau** numéro, l'identifiant ne change
// qu'à la vérification, l'ancien numéro reçoit un message d'information, et la session en cours
// **survit** au changement. Une personne qui corrige son numéro n'a pas à se reconnecter.
import { existsSync, readFileSync } from 'node:fs'
import { expect, test } from '@playwright/test'
import { ETAT_SESSION } from '../portes/outils'

const JOURNAL = process.env.NELO_SMS_JOURNAL ?? ''
const ANCIEN = process.env.NUMERO_A ?? ''
const NOUVEAU = '+2250700008888'
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

function soumettre(page: import('@playwright/test').Page) {
  return page.locator('form button[type="submit"]')
}

test.use({ viewport: { width: 390, height: 844 }, storageState: ETAT_SESSION })

test('le code part vers le nouveau numéro, et l’ancien est informé après la vérification', async ({
  page,
}) => {
  expect(ANCIEN, 'NUMERO_A n’est pas posé').not.toBe('')
  const dejaNouveau = envoisVers(NOUVEAU).length
  const dejaAncien = envoisVers(ANCIEN).length

  await page.goto('/compte/telephone')
  await page.getByRole('textbox').first().fill(NOUVEAU.replace(/^\+225/, ''))
  await soumettre(page).click()

  const code = await attendreCode(NOUVEAU, dejaNouveau)
  // Rien n'est encore parti vers l'ancien : l'identifiant ne change qu'à la vérification.
  expect(envoisVers(ANCIEN).length).toBe(dejaAncien)

  await page.getByRole('textbox').first().fill(code)
  await soumettre(page).click()

  // Le changement est annoncé, et la session tient : aucun retour à l'écran de connexion.
  await expect(page.getByText(/changé/i).first()).toBeVisible({ timeout: 15000 })
  await expect(page).not.toHaveURL(/\/connexion/)

  // L'ancien numéro reçoit son message d'information, une fois le changement fait.
  for (let essai = 0; essai < 100; essai++) {
    if (envoisVers(ANCIEN).length > dejaAncien) break
    await new Promise((resoudre) => setTimeout(resoudre, 100))
  }
  expect(envoisVers(ANCIEN).length, 'l’ancien numéro doit être informé').toBeGreaterThan(dejaAncien)
  expect(envoisVers(ANCIEN).pop()!.texte).toContain(NOUVEAU)
})
