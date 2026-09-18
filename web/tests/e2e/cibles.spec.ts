// US8 : aucune cible interactive sous 44 px, 52 en classe, 48 au standard (05-design.md § 3).
import { expect, test } from '@playwright/test'
import { PORT_DEV } from '../portes/outils'

const ECRANS = [
  { adresse: '/?persona=sept-domaines', minimum: 48 },
  { adresse: '/d/vie_scolaire?persona=un-domaine', minimum: 52 },
  { adresse: '/a-propos?persona=un-domaine', minimum: 48 },
  { adresse: `http://localhost:${PORT_DEV}/style`, minimum: 44 },
]
const INTERACTIFS = 'a, button, input, select, [role="switch"], [role="tab"]'

for (const largeur of [390, 1200]) {
  for (const { adresse, minimum } of ECRANS) {
    test(`${largeur} px, ${adresse} : chaque cible mesure au moins ${minimum} px`, async ({ page }) => {
      await page.setViewportSize({ width: largeur, height: 844 })
      await page.goto(adresse, { timeout: 60_000 })
      await expect(page.locator('main')).toBeVisible()
      const petites = await page.locator(INTERACTIFS).evaluateAll((elements, seuil) => {
        const fautives: string[] = []
        for (const el of elements) {
          const boite = el.getBoundingClientRect()
          const style = getComputedStyle(el)
          if (boite.width === 0 || style.visibility === 'hidden' || style.display === 'none') continue
          if (el.closest('[data-contexte-tactile="poste"]')) {
            // Un contrôle de poste se dessine à 36 px et garde 44 px de zone par un pseudo-élément.
            const zone = parseFloat(getComputedStyle(el, '::before').height) || 0
            if (Math.max(boite.height, zone) < 44 || boite.width < 44) fautives.push(el.outerHTML.slice(0, 80))
            continue
          }
          const attendu = el.closest('[data-theme]') && el.closest('.theme') ? 44 : seuil
          if (boite.height < attendu - 0.5 || boite.width < 44 - 0.5) {
            fautives.push(`${Math.round(boite.width)}×${Math.round(boite.height)} ${el.outerHTML.slice(0, 80)}`)
          }
        }
        return fautives
      }, minimum)
      expect(petites).toEqual([])
    })
  }
}
