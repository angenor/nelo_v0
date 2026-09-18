// US4 : la coquille de T0b vit sur le contexte réel, sans changer d'écran.
//
// Ce que cette suite prouve : la session semée n'a aucune capacité (T1b les livrera), et l'écran
// « aucun domaine » nomme alors **une vraie personne**, celle que l'établissement a désignée ;
// le compte rattaché à deux établissements choisit, et la coquille se relit ; le choix vit sur
// l'appareil, jamais côté serveur.
import { expect, test } from '@playwright/test'
import { ETAT_SESSION } from '../portes/outils'

test.use({ viewport: { width: 390, height: 844 }, storageState: ETAT_SESSION })

test('sans capacité, l’accueil nomme l’administrateur de l’établissement', async ({ page }) => {
  await page.goto('/')

  const sans = page.locator('section[data-situation="AUCUNE_CAPACITE"]')
  await expect(sans).toBeVisible()
  // Un nom et un numéro, pas « contactez votre administrateur » : on doit savoir qui appeler.
  const texte = await sans.innerText()
  expect(texte).toMatch(/Koné/)
  expect(texte).toMatch(/\d{2}/)
})

test('le choix d’établissement se fait sur l’appareil, et rien n’est gardé côté serveur', async ({
  page,
  browser,
}) => {
  await page.goto('/')

  // Le compte du jeu d'essai est rattaché à deux établissements : le menu les propose.
  await page.locator('[data-menu-compte]').click()
  const etablissements = page.locator('[data-panneau-compte] section').first().locator('button.ligne')
  await expect(etablissements).toHaveCount(2)

  const second = etablissements.nth(1)
  const nom = (await second.innerText()).trim()
  await second.click()

  // Le menu se relit sur le contexte du nouvel établissement : c'est lui qui porte la coche.
  await page.locator('[data-menu-compte]').click()
  const actif = page
    .locator('[data-panneau-compte] section')
    .first()
    .locator('button.ligne[aria-current="true"]')
  await expect(actif).toContainText(nom.split('\n').pop()!.trim())

  // Un navigateur neuf, la même session : le choix ne l'a pas suivi, il vit sur l'appareil.
  const autre = await browser.newContext({
    storageState: ETAT_SESSION,
    viewport: { width: 390, height: 844 },
  })
  try {
    const pageNeuve = await autre.newPage()
    await pageNeuve.goto('/')
    await pageNeuve.locator('[data-menu-compte]').click()
    const premier = pageNeuve
      .locator('[data-panneau-compte] section')
      .first()
      .locator('button.ligne[aria-current="true"]')
    await expect(premier).not.toContainText(nom.split('\n').pop()!.trim())
  } finally {
    await autre.close()
  }
})
