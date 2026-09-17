// US4 : le parcours complet se fait dans la coquille, sans rechargement ; un lien profond se
// résout dans la coquille (FR-029, FR-041).
import { expect, test } from '@playwright/test'

test('accueil → domaine → à propos → retour, sans aucun rechargement', async ({ page }) => {
  let chargements = 0
  page.on('load', () => chargements++)
  await page.goto('/?persona=cinq-domaines')
  await expect(page.locator('[data-hydrate]')).toHaveCount(1)
  await page.locator('[data-bloc-domaine="vie_scolaire"]').click()
  await expect(page).toHaveURL(/\/d\/vie_scolaire$/)
  await expect(page.getByRole('heading', { name: 'CM2 A' })).toBeVisible()
  await page.getByRole('link', { name: 'À propos' }).click()
  await expect(page).toHaveURL(/\/a-propos$/)
  await expect(page.getByRole('heading', { level: 1 })).toContainText('À propos')
  await page.getByRole('button', { name: 'Retour' }).click()
  await expect(page).toHaveURL(/\/d\/vie_scolaire$/)
  await page.getByRole('link', { name: /^Accueil/ }).click()
  await expect(page).toHaveURL(/\/$/)
  await expect(page.locator('[data-bloc-domaine]')).toHaveCount(5)
  expect(chargements).toBe(1)
})

test('un lien profond se rend dans la coquille', async ({ page }) => {
  await page.goto('/d/vie_scolaire')
  await expect(page.locator('header.entete')).toBeVisible()
  await expect(page.locator('[data-situation="MONO_DOMAINE"]')).toBeVisible()
  await expect(page.getByRole('status', { name: 'État de la saisie' })).toBeVisible()
})

test('un domaine que la personne ne détient pas renvoie à son accueil', async ({ page }) => {
  await page.goto('/d/finance?persona=cinq-domaines')
  await expect(page).toHaveURL(/\/\?persona=cinq-domaines$/)
})
