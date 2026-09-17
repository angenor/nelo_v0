// US5 : tout ce qui est visible suit la langue, sans rechargement ; les mots métier suivent le
// pack ; aucune clé brute n'est jamais affichée (FR-050 à FR-054).
import type { Page } from '@playwright/test'
import { expect, test } from '@playwright/test'

// Ce qui ne se traduit pas : noms propres, identifiants, chiffres, codes de langue, marques.
const INVARIANTS = [
  /^[\d\s:·/.,+−\-–%|]*$/,
  /^(FR|EN|GS|SMS|WhatsApp)$/,
  /Groupe Scolaire Les Palmiers/,
  /^Angré$/,
  /^CM2( A)?$/,
  /^2026-2027$/,
  /^(Mme |M\. )?(Aline Kacou|Bakary Sanogo|Adjoua N’Guessan|Yao Serge Emmanuel|Diabaté Fatoumata|Bamba Ousmane)$/,
  /^[A-Z]{2}$/,
  /ELV-\d{4}-\d{4}|REC-\d{6}/,
]

async function textes(page: Page): Promise<string[]> {
  const brut = await page.locator('body').innerText()
  return [...new Set(brut.split('\n').map((l) => l.trim()).filter(Boolean))]
}

for (const ecran of ['/d/vie_scolaire?persona=un-domaine', '/?persona=sept-domaines']) {
  test(`FR → EN sur ${ecran} : chaque libellé change, aucune clé brute`, async ({ page }) => {
    await page.goto(ecran)
    await expect(page.locator('[data-hydrate]')).toHaveCount(1)
    await expect(page.locator('html')).toHaveAttribute('lang', 'fr')
    const avant = await textes(page)
    await page.getByRole('group', { name: 'Langue de l’interface' }).getByRole('button', { name: 'EN', exact: true }).click()
    await expect(page.locator('html')).toHaveAttribute('lang', 'en')
    await expect(page.getByRole('group', { name: 'Interface language' })).toBeVisible()
    const apres = await textes(page)
    const restes = apres.filter((l) => avant.includes(l) && !INVARIANTS.some((r) => r.test(l)))
    expect(restes).toEqual([])
    for (const ligne of [...avant, ...apres]) expect(ligne).not.toMatch(/^[a-z_]+(\.[A-Za-z_]+)+$/)
  })
}

test('le mot métier suit la langue et le pack', async ({ page }) => {
  await page.goto('/d/vie_scolaire?persona=un-domaine')
  await expect(page.locator('[data-mot-pack="CLASSE"]')).toHaveText('Classe')
  await expect(page.locator('main')).toContainText('Maître titulaire')
  await page.getByRole('button', { name: 'EN', exact: true }).click()
  await expect(page.locator('[data-mot-pack="CLASSE"]')).toHaveText('Class')
  await expect(page.locator('main')).toContainText('Class teacher')
})

test('le pack fictif change « classe » sans une ligne de code', async ({ page }) => {
  await page.goto('/d/vie_scolaire?persona=un-domaine&pack=fictif')
  await expect(page.locator('[data-mot-pack="CLASSE"]')).toHaveText('Form')
  await expect(page.locator('main')).toContainText('Maître titulaire')
})
