// US1 : aucun état n'est porté par la couleur seule, l'attente parle en ocre, et le rouge
// n'appartient qu'à l'impayé et à l'absence non justifiée (FR-005).
import { expect, test } from '@playwright/test'
import { PORT_DEV } from '../portes/outils'

test.beforeEach(async ({ page }) => {
  await page.goto(`http://localhost:${PORT_DEV}/style`, { timeout: 60_000 })
})

test('chaque pastille, alerte et ruban porte une forme et un mot', async ({ page }) => {
  const porteurs = page.locator('[data-porteur-etat]')
  expect(await porteurs.count()).toBeGreaterThan(20)
  for (const el of await porteurs.all()) {
    await expect(el).toHaveAttribute('data-forme', /\S/)
    expect((await el.innerText()).trim()).not.toBe('')
  }
})

test('les états d’attente parlent en ocre', async ({ page }) => {
  for (const code of ['EN_ATTENTE', 'ECHEANCE_PROCHE', 'NON_FAIT']) {
    const pastilles = page.locator(`[data-code="${code}"]`)
    expect(await pastilles.count(), code).toBeGreaterThan(0)
    for (const p of await pastilles.all()) await expect(p).toHaveAttribute('data-voix', 'ocre')
  }
  for (const a of await page.locator('[data-niveau="attente"]').all()) {
    await expect(a).toHaveAttribute('data-voix', 'ocre')
  }
})

test('seuls l’impayé et l’absence non justifiée parlent en rouge', async ({ page }) => {
  const rouges = await page
    .locator('[data-code][data-voix="rouge"]')
    .evaluateAll((els) => [...new Set(els.map((e) => e.getAttribute('data-code')))].sort())
  expect(rouges).toEqual(['IMPAYE', 'NON_JUSTIFIE'])
  await expect(page.locator('[data-composant="RubanSaisie"] [data-voix="rouge"]')).toHaveCount(0)
})
