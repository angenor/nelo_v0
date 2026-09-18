// R-21, FR-051 : l'établissement et l'année de travail vivent **sur l'appareil**.
//
// Ce que ces tests tiennent : rien n'est gardé côté serveur, une chaîne vide n'est pas un choix,
// et effacer un choix le fait disparaître au lieu de le remplacer par du vide. Le stockage est
// fabriqué ici : ces fonctions ne doivent rien connaître du navigateur.
import { describe, expect, it } from 'vitest'
import {
  ecrireAnneeChoisie,
  ecrireEtablissementChoisi,
  lireAnneeChoisie,
  lireEtablissementChoisi,
} from '../../app/core/appareil/choix'
import type { Stockage } from '../../app/core/plateforme/plateforme'

/** Un stockage de papier : ce que la plateforme fournit, réduit à ce que ces fonctions lisent. */
function stockageFabrique(depart: Record<string, string> = {}): Stockage & {
  contenu: Record<string, string>
} {
  const contenu = { ...depart }
  return {
    contenu,
    disponible: true,
    lire: (cle) => (cle in contenu ? contenu[cle]! : null),
    ecrire: (cle, valeur) => {
      contenu[cle] = valeur
    },
    effacer: (cle) => {
      delete contenu[cle]
    },
  }
}

const ETABLISSEMENT = '01900000-0000-7000-8000-000000000001'
const ANNEE = '01900000-0000-7000-8000-000000000002'

describe('le choix d’établissement', () => {
  it('n’existe pas tant que personne ne l’a fait', () => {
    expect(lireEtablissementChoisi(stockageFabrique())).toBeNull()
  })

  it('se lit tel qu’il a été écrit', () => {
    const stockage = stockageFabrique()
    ecrireEtablissementChoisi(stockage, ETABLISSEMENT)
    expect(lireEtablissementChoisi(stockage)).toBe(ETABLISSEMENT)
  })

  it('s’efface, et ne laisse pas une chaîne vide derrière lui', () => {
    const stockage = stockageFabrique()
    ecrireEtablissementChoisi(stockage, ETABLISSEMENT)
    ecrireEtablissementChoisi(stockage, null)
    expect(lireEtablissementChoisi(stockage)).toBeNull()
    expect(Object.keys(stockage.contenu)).toHaveLength(0)
  })

  it('tient une chaîne vide pour une absence de choix, jamais pour un choix', () => {
    const stockage = stockageFabrique({ etablissement: '' })
    expect(lireEtablissementChoisi(stockage)).toBeNull()
    ecrireEtablissementChoisi(stockage, '')
    expect(lireEtablissementChoisi(stockage)).toBeNull()
  })
})

describe('le choix d’année', () => {
  it('se lit et s’efface comme celui de l’établissement', () => {
    const stockage = stockageFabrique()
    expect(lireAnneeChoisie(stockage)).toBeNull()
    ecrireAnneeChoisie(stockage, ANNEE)
    expect(lireAnneeChoisie(stockage)).toBe(ANNEE)
    ecrireAnneeChoisie(stockage, null)
    expect(lireAnneeChoisie(stockage)).toBeNull()
  })

  it('ne se mélange pas avec celui de l’établissement', () => {
    const stockage = stockageFabrique()
    ecrireEtablissementChoisi(stockage, ETABLISSEMENT)
    ecrireAnneeChoisie(stockage, ANNEE)
    expect(lireEtablissementChoisi(stockage)).toBe(ETABLISSEMENT)
    expect(lireAnneeChoisie(stockage)).toBe(ANNEE)

    ecrireAnneeChoisie(stockage, null)
    expect(lireEtablissementChoisi(stockage)).toBe(ETABLISSEMENT)
  })
})
