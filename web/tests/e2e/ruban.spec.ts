// US2 : le ruban dit trois choses, suit le réseau, et ne bloque jamais la saisie (FR-010 à FR-016).
import { expect, test } from '@playwright/test'
import { SONDE_RESEAU, reseau } from './reseau'

const ECRAN = '/d/vie_scolaire?persona=un-domaine'

test.beforeEach(async ({ page }) => {
  await page.addInitScript(SONDE_RESEAU)
  await page.goto(ECRAN)
  await expect(page.locator('[data-hydrate]')).toHaveCount(1)
})

async function saisir(page: import('@playwright/test').Page, texte: string) {
  const champ = page.getByLabel('Observation du jour')
  await champ.fill(texte)
  await champ.press('Enter')
}

test('lien bon : « Tout est enregistré »', async ({ page }) => {
  const ruban = page.getByRole('status', { name: 'État de la saisie' })
  await expect(ruban).toContainText('Tout est enregistré')
  await expect(ruban).toHaveAttribute('data-voix', 'reussite')
  await expect(ruban).toContainText('Lien bon')
})

test('lien faible : « Envoi de 2 saisies », le point pulse, puis tout part', async ({ page, context }) => {
  await reseau(page, context, 'faible')
  const ruban = page.getByRole('status', { name: 'État de la saisie' })
  await expect(ruban).toContainText('Lien faible')
  await saisir(page, 'Sortie au musée jeudi')
  await saisir(page, 'Cahier oublié')
  await expect(ruban).toContainText('Envoi de 2 saisies')
  await expect(ruban).toHaveAttribute('data-forme', 'point')
  const animation = await ruban.locator('.point').evaluate((e) => getComputedStyle(e).animationName)
  expect(animation).not.toBe('none')
  await expect(ruban).toContainText('Tout est enregistré', { timeout: 5_000 })
})

test('hors ligne : le compte monte, rien n’est grisé, et le retour du lien vide la file sans geste', async ({
  page,
  context,
}) => {
  const controlesAvant = await page.locator('[disabled], [aria-disabled]').count()
  await reseau(page, context, 'absent')
  const ruban = page.getByRole('status', { name: 'État de la saisie' })
  await expect(ruban).toContainText('Hors ligne')
  await expect(ruban).toHaveAttribute('data-voix', 'ocre')
  for (const texte of ['Un', 'Deux', 'Trois', 'Quatre']) await saisir(page, texte)
  await expect(ruban).toContainText('4 saisies conservées')
  await expect(ruban).toHaveAttribute('data-en-attente', '4')
  expect(await page.locator('[disabled], [aria-disabled]').count()).toBe(controlesAvant)
  await expect(page.getByLabel('Observation du jour')).toBeEditable()

  await reseau(page, context, 'bon')
  await expect(ruban).toContainText('Tout est enregistré', { timeout: 2_000 })
  await expect(ruban).toHaveAttribute('data-en-attente', '0')
})

test('sous « réduire les animations », le point ne pulse plus, la forme et le mot restent', async ({
  page,
  context,
}) => {
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await reseau(page, context, 'faible')
  await saisir(page, 'Une observation')
  const ruban = page.getByRole('status', { name: 'État de la saisie' })
  await expect(ruban).toHaveAttribute('data-forme', 'point')
  await expect(ruban.locator('.point')).toBeVisible()
  expect(await ruban.locator('.point').evaluate((e) => getComputedStyle(e).animationName)).toBe('none')
  await expect(ruban).toContainText('Envoi d’une saisie')
})

test('le ruban reste visible au défilement et ne recouvre pas l’action principale', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 600 })
  await page.locator('main#principal').evaluate((e) => e.scrollTo(0, e.scrollHeight))
  const ruban = page.getByRole('status', { name: 'État de la saisie' })
  await expect(ruban).toBeInViewport()
  const principal = page.locator('.bouton--principal')
  await expect(principal).toBeInViewport()
  const a = (await ruban.boundingBox())!
  const b = (await principal.boundingBox())!
  const chevauchement = a.y < b.y + b.height && b.y < a.y + a.height && a.x < b.x + b.width && b.x < a.x + a.width
  expect(chevauchement).toBe(false)
})
