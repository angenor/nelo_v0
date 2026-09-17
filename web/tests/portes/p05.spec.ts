// PORTE P-05 : chaque écran déclaré s'atteint dans un vrai navigateur, sur deux moteurs et deux
// thèmes, sans erreur de page ni de console (research.md R-12). Monter un composant dans un test
// ne prouve pas qu'une page s'atteint.
import { readdirSync, readFileSync } from 'node:fs'
import { join, relative } from 'node:path'
import { expect, test } from '@playwright/test'
import { ECRANS, THEMES, scriptTheme, visites } from './outils'

const PAGES = join(import.meta.dirname, '../../app/pages')

function routesDesPages(dossier = PAGES): string[] {
  return readdirSync(dossier, { withFileTypes: true }).flatMap((entree) => {
    const chemin = join(dossier, entree.name)
    if (entree.isDirectory()) return routesDesPages(chemin)
    if (!entree.name.endsWith('.vue')) return []
    const route = '/' + relative(PAGES, chemin).replace(/\.vue$/, '').replace(/(^|\/)index$/, '')
    return [route.replace(/\/$/, '') || '/']
  })
}

function correspond(motif: string, route: string): boolean {
  const expression = motif.replace(/\[[^\]]+\]/g, '[^/]+')
  return new RegExp(`^${expression}$`).test(route)
}

test('P-05 : chaque page de web/app/pages est déclarée dans ecrans.json', () => {
  for (const motif of routesDesPages()) {
    const declare = ECRANS.some((e) => correspond(motif, e.route))
    if (!declare) throw new Error(`PORTE P-05 ÉCHOUÉE : écran non déclaré ${motif}`)
  }
})

for (const visite of visites()) {
  for (const theme of THEMES) {
    test(`P-05 : ${visite.nom}, thème ${theme}`, async ({ page, browserName }) => {
      const erreurs: string[] = []
      page.on('pageerror', (e) => erreurs.push(`erreur de page : ${e.message}`))
      page.on('console', (m) => {
        if (m.type() === 'error') erreurs.push(`console : ${m.text()}`)
      })
      const echec = (motif: string) =>
        `PORTE P-05 ÉCHOUÉE : écran ${visite.nom}, moteur ${browserName}, thème ${theme} : ${motif}`

      await page.addInitScript(scriptTheme(theme))
      const reponse = await page.goto(visite.adresse, { timeout: 60_000 }).catch((e: Error) => {
        throw new Error(echec(`navigation impossible (${e.message.split('\n')[0]})`))
      })
      expect(reponse?.status(), echec(`statut ${reponse?.status()}`)).toBeLessThan(400)
      await expect(page.locator('main#principal'), echec('repère main#principal absent')).toBeVisible()
      await expect(page.locator('html'), echec('thème non appliqué')).toHaveAttribute('data-theme', theme)
      await page.waitForLoadState('networkidle')
      expect(erreurs, echec(erreurs.join(' | '))).toEqual([])
    })
  }
}

test.describe('P-05 : installabilité', () => {
  const racine = join(import.meta.dirname, '../../..')
  const jetons = JSON.parse(readFileSync(join(racine, 'docs/design/tokens.json'), 'utf8'))
  const produit = readFileSync(join(racine, 'web/app/core/produit.ts'), 'utf8')
  const nom = /export const NOM = '([^']+)'/.exec(produit)?.[1]
  const nomCourt = /export const NOM_COURT = '([^']+)'/.exec(produit)?.[1]

  test('le manifeste est servi, autonome, nommé, coloré par les jetons, avec ses icônes', async ({ page, request, browserName }) => {
    const echec = (motif: string) => `PORTE P-05 ÉCHOUÉE : installabilité, moteur ${browserName} : ${motif}`
    await page.goto('/')
    const lien = await page.locator('link[rel="manifest"]').getAttribute('href')
    expect(lien, echec('aucun lien vers le manifeste')).toBeTruthy()
    const reponse = await request.get(lien!)
    expect(reponse.ok(), echec(`manifeste ${lien} introuvable`)).toBe(true)
    const manifeste = await reponse.json()
    expect(manifeste.display, echec('affichage non autonome')).toBe('standalone')
    expect([manifeste.name, manifeste.short_name], echec('nom du manifeste')).toEqual([nom, nomCourt])
    expect(manifeste.theme_color?.toUpperCase(), echec('theme_color')).toBe(jetons.clair['--primary'])
    expect(manifeste.background_color?.toUpperCase(), echec('background_color')).toBe(jetons.clair['--bg'])
    const tailles = manifeste.icons.map((i: { sizes: string }) => i.sizes)
    expect(tailles, echec('icônes 192 et 512')).toEqual(expect.arrayContaining(['192x192', '512x512']))
    expect(manifeste.icons.some((i: { purpose?: string }) => i.purpose?.includes('maskable')), echec('icône maskable')).toBe(true)
    for (const icone of manifeste.icons) {
      const image = await request.get(icone.src)
      expect(image.ok(), echec(`icône ${icone.src} introuvable`)).toBe(true)
      expect(image.headers()['content-type'], echec(`icône ${icone.src} n’est pas un PNG`)).toContain('image/png')
    }
    await expect(page.locator('link[rel="apple-touch-icon"]'), echec('apple-touch-icon')).toHaveCount(1)
    await expect(page.locator('meta[name="apple-mobile-web-app-capable"]'), echec('apple-mobile-web-app-capable')).toHaveCount(1)
  })

  test('le service worker s’enregistre et contrôle la page (Chromium)', async ({ page, browserName }) => {
    test.skip(browserName !== 'chromium', 'WebKit sans tête n’expose pas le contrôle du service worker')
    await page.goto('/')
    await page.evaluate(() => navigator.serviceWorker.ready.then(() => true))
    await page.reload()
    const controle = await page.evaluate(() => navigator.serviceWorker.controller !== null)
    expect(controle, 'PORTE P-05 ÉCHOUÉE : installabilité, le service worker ne contrôle pas la page').toBe(true)
  })
})
