// US6 : le lien d'activation, dans un navigateur réel.
//
// Ce que cette suite prouve : un lien reçu par SMS ouvre une session et mène au code personnel ;
// le même lien, rouvert, ne vaut plus rien et dit **les deux façons de continuer** au lieu de
// laisser la personne devant une impasse ; un lien inventé donne le même refus, jamais une erreur
// technique.
//
// Le compte est créé par l'API, avec la session semée : c'est le geste du secrétariat. Le lien se
// lit là où la personne le lirait, dans le message.
import { existsSync, readFileSync } from 'node:fs'
import { expect, request, test } from '@playwright/test'
import { uuid7 } from '../../app/core/api/uuid7'
import { ETAT_SESSION } from '../portes/outils'

const JOURNAL = process.env.NELO_SMS_JOURNAL ?? ''
const ETAB = process.env.ETAB_A ?? ''
const PERSONNE = process.env.PERSONNE_NOUVELLE ?? ''
const LIEN = /\/activation\/([A-Za-z0-9_-]+)/

interface EnvoiJournalise {
  destinataire: string
  texte: string
}

function envois(): EnvoiJournalise[] {
  if (!existsSync(JOURNAL)) return []
  return readFileSync(JOURNAL, 'utf8')
    .split('\n')
    .filter((ligne) => ligne.trim() !== '')
    .map((ligne) => JSON.parse(ligne) as EnvoiJournalise)
}

async function attendreLien(deja: number): Promise<string> {
  for (let essai = 0; essai < 100; essai++) {
    const tous = envois()
    for (const envoi of tous.slice(deja)) {
      const trouve = LIEN.exec(envoi.texte)?.[1]
      if (trouve) return trouve
    }
    await new Promise((resoudre) => setTimeout(resoudre, 100))
  }
  throw new Error(`aucun lien d'activation dans ${JOURNAL}`)
}

test.use({ viewport: { width: 390, height: 844 }, storageState: { cookies: [], origins: [] } })

test('un lien reçu active le compte, une fois et une seule', async ({ page, baseURL }) => {
  expect(PERSONNE, 'PERSONNE_NOUVELLE n’est pas posé').not.toBe('')
  const deja = envois().length

  // Le secrétariat crée le compte : c'est la session semée qui en a le droit.
  const secretariat = await request.newContext({ baseURL, storageState: ETAT_SESSION })
  try {
    const creation = await secretariat.post('/api/v1/comptes', {
      headers: { 'X-Nelo-Requete': uuid7(), 'X-Nelo-Etablissement': ETAB },
      data: { personne_id: PERSONNE, identifiant: '+2250700007777' },
    })
    expect(creation.status(), await creation.text()).toBe(201)
    // La réponse dit la date d'envoi, jamais le lien : il ne passe que par le message.
    expect(await creation.text()).not.toContain('activation/')
  } finally {
    await secretariat.dispose()
  }

  const jeton = await attendreLien(deja)

  await page.goto(`/activation/${jeton}`)
  // La session s'ouvre et l'étape du code personnel suit.
  await page.waitForURL(/\/connexion\/pin$|localhost:\d+\/$/, { timeout: 15000 })

  // Le même lien, rouvert : il ne vaut plus rien, et l'écran dit par où continuer.
  await page.context().clearCookies()
  await page.goto(`/activation/${jeton}`)
  await expect(page.getByRole('heading', { name: /ne fonctionne plus/i })).toBeVisible()
  await expect(page.getByRole('link', { name: /numéro/i })).toBeVisible()
})

test('un lien inventé donne le refus, jamais une erreur technique', async ({ page }) => {
  await page.goto('/activation/jeton-qui-n-a-jamais-existe')

  await expect(page.getByRole('heading', { name: /ne fonctionne plus/i })).toBeVisible()
  const texte = (await page.locator('body').innerText()).toLowerCase()
  expect(texte).not.toContain('erreur interne')
  expect(texte).not.toContain('500')
})
