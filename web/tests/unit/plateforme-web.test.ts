// Hors navigateur, chaque capacité répond « indisponible » sans lever (FR-043).
import { describe, expect, it } from 'vitest'
import { PLATEFORME_INDISPONIBLE } from '../../app/core/plateforme/indisponible'
import { creerPlateformeWeb } from '../../app/core/plateforme/web'

describe('la plateforme web, là où le navigateur ne dit rien', () => {
  const plateforme = creerPlateformeWeb()

  it('se dit en bon réseau et accepte un abonnement', () => {
    expect(plateforme.reseau.etat).toBe('bon')
    const desabonner = plateforme.reseau.surChangement(() => {})
    expect(() => desabonner()).not.toThrow()
  })

  it('se dit en apparence claire hors navigateur', () => {
    expect(plateforme.apparence.sombre).toBe(false)
    expect(() => plateforme.apparence.surChangement(() => {})()).not.toThrow()
  })

  it('nomme un raccourci et accepte un abonnement sans fenêtre', () => {
    expect(plateforme.clavier.libelle('k')).toMatch(/^(Ctrl|⌘) K$/)
    expect(() => plateforme.clavier.surRaccourci('k', () => {})()).not.toThrow()
  })

  it('ne lève jamais sur le stockage', () => {
    expect(() => plateforme.stockage.ecrire('theme', 'dark')).not.toThrow()
    expect(() => plateforme.stockage.effacer('theme')).not.toThrow()
    if (!plateforme.stockage.disponible) expect(plateforme.stockage.lire('theme')).toBeNull()
  })

  it('rend null à la capture et « refusee » à la demande de notification', async () => {
    expect(plateforme.camera.disponible).toBe(false)
    await expect(plateforme.camera.capturer()).resolves.toBeNull()
    expect(plateforme.notifications.disponible).toBe(false)
    await expect(plateforme.notifications.demander()).resolves.toBe('refusee')
    expect(() => plateforme.notifications.afficher('t', 'c')).not.toThrow()
  })
})

describe('la plateforme du rendu serveur', () => {
  it('répond indisponible partout', async () => {
    const p = PLATEFORME_INDISPONIBLE
    expect(p.stockage.disponible).toBe(false)
    expect(p.stockage.lire('x')).toBeNull()
    await expect(p.camera.capturer()).resolves.toBeNull()
    await expect(p.notifications.demander()).resolves.toBe('refusee')
  })
})
