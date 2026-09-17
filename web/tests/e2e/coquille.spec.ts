// US3 : quatre personas, quatre situations, à 390 et à 1200 px ; aucune entrée grisée.
import { expect, test } from '@playwright/test'

for (const largeur of [390, 1200]) {
  test.describe(`à ${largeur} px`, () => {
    test.use({ viewport: { width: largeur, height: 844 } })
    const navigation = largeur < 768 ? 'nav.disposition-basse' : 'nav.disposition-laterale'

    test('un domaine : l’accueil est le domaine, trois entrées, aucune famille', async ({ page }) => {
      await page.goto('/?persona=un-domaine')
      await expect(page).toHaveURL(/\/d\/vie_scolaire/)
      await expect(page.locator('[data-situation="MONO_DOMAINE"]')).toBeVisible()
      await expect(page.locator(`${navigation} a[data-entree]`)).toHaveCount(3)
      await expect(page.locator('.famille')).toHaveCount(0)
    })

    test('cinq domaines : tableau composé de cinq blocs, navigation à plat de cinq', async ({ page }) => {
      await page.goto('/?persona=cinq-domaines')
      await expect(page.locator('[data-situation="MULTI_PLAT"]')).toBeVisible()
      await expect(page.locator('[data-bloc-domaine]')).toHaveCount(5)
      await expect(page.locator(`${navigation} a[data-domaine]`)).toHaveCount(5)
      await expect(page.locator('.famille')).toHaveCount(0)
      const alerte = page.locator('[data-alerte="BUDGET_SMS_BAS"]')
      await expect(alerte).toHaveAttribute('data-niveau', 'attente')
    })

    test('sept domaines : familles présentes et non vides', async ({ page }) => {
      await page.goto('/?persona=sept-domaines')
      await expect(page.locator('[data-situation="MULTI_FAMILLES"]')).toBeVisible()
      if (largeur < 768) {
        await expect(page.locator('nav.disposition-laterale')).toBeHidden()
        await page.getByRole('button', { name: /ouvrir le menu/i }).click()
        await expect(page.locator('nav.disposition-tiroir')).toBeVisible()
      }
      const nav = page.locator(largeur < 768 ? 'nav.disposition-tiroir' : 'nav.disposition-laterale')
      await expect(nav.locator('.famille')).toHaveText(['Élèves', 'Enseignement', 'Gestion', 'Communication'])
      for (const groupe of await nav.locator('.groupe').all()) {
        expect(await groupe.locator('a[data-domaine]').count()).toBeGreaterThan(0)
      }
      await expect(nav.locator('a[data-domaine]')).toHaveCount(7)
    })

    test('aucune capacité : pas de navigation, l’administrateur nommé, la demande proposée', async ({ page }) => {
      await page.goto('/?persona=aucune-capacite')
      await expect(page.locator('[data-situation="AUCUNE_CAPACITE"]').first()).toBeVisible()
      await expect(page.locator('nav[aria-label="Navigation principale"]')).toHaveCount(0)
      await expect(page.locator('[data-administrateur]')).toContainText('Konan Bertin')
      await expect(page.locator('[data-administrateur]')).toContainText('01 02 03 04 05')
      await expect(page.getByRole('link', { name: 'Demander mes accès' })).toBeVisible()
    })

    test('aucune entrée grisée, et l’en-tête complet, pour chaque persona', async ({ page }) => {
      for (const persona of ['un-domaine', 'cinq-domaines', 'sept-domaines', 'aucune-capacite']) {
        await page.goto(`/?persona=${persona}`)
        await expect(page.locator('nav [aria-disabled], nav .grise, nav [disabled]')).toHaveCount(0)
        const entete = page.locator('header.entete')
        await expect(entete).toContainText('Groupe Scolaire Les Palmiers')
        await expect(entete).toContainText('Angré')
        await expect(entete.getByRole('group', { name: 'Langue de l’interface' })).toBeVisible()
        await expect(entete.getByRole('img', { name: /^Compte : / })).toBeVisible()
        if (largeur >= 768) await expect(entete).toContainText('2026-2027')
      }
    })
  })
}
