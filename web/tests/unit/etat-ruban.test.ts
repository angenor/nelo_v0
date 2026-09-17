// US2 : l'état du ruban est dérivé, jamais posé ; la table de data-model.md § 3, ligne par ligne.
import { describe, expect, it } from 'vitest'
import { COMPOSANTS } from '../../app/core/composants/etats'
import { deriverEtatRuban } from '../../app/core/saisie/etat-ruban'

const dix_heures = new Date('2026-08-18T10:42:00')

describe('deriverEtatRuban', () => {
  it.each([
    ['bon', 0, 'enregistre', 'reussite', 'coche'],
    ['faible', 0, 'enregistre', 'reussite', 'coche'],
    ['bon', 2, 'envoi', 'marque', 'point'],
    ['faible', 2, 'envoi', 'marque', 'point'],
    ['absent', 0, 'hors_ligne', 'ocre', 'lien_barre'],
    ['absent', 4, 'hors_ligne', 'ocre', 'lien_barre'],
  ] as const)('réseau %s, %i en attente → %s, voix %s, forme %s', (reseau, attente, etat, voix, forme) => {
    const vue = deriverEtatRuban(reseau, attente, dix_heures)
    expect([vue.etat, vue.voix, vue.forme]).toEqual([etat, voix, forme])
  })

  it('dit les trois choses avec leurs clés', () => {
    expect(deriverEtatRuban('bon', 0, dix_heures)).toMatchObject({
      titre: { cle: 'ruban.enregistre' },
      moment: { cle: 'ruban.dernier_a', heure: dix_heures },
      consigne: { cle: 'ruban.aucune_attente' },
      lien: { cle: 'ruban.lien_bon', barres: 3 },
    })
    expect(deriverEtatRuban('faible', 2, dix_heures)).toMatchObject({
      titre: { cle: 'ruban.envoi_de', params: { n: 2 } },
      consigne: { cle: 'ruban.continuez' },
      lien: { cle: 'ruban.lien_faible', barres: 2 },
    })
    expect(deriverEtatRuban('absent', 4, dix_heures)).toMatchObject({
      titre: { cle: 'ruban.hors_ligne' },
      moment: { cle: 'ruban.conservees', params: { n: 4 } },
      consigne: { cle: 'ruban.rien_perdu' },
      lien: { cle: 'ruban.pas_de_lien', barres: 0 },
    })
  })

  it('dit l’absence d’enregistrement en mots, jamais « 00:00 »', () => {
    expect(deriverEtatRuban('bon', 0, null).moment).toEqual({ cle: 'ruban.aucun_enregistrement', heure: null })
  })

  it('dit « aucune saisie en attente » hors ligne quand rien n’attend', () => {
    expect(deriverEtatRuban('absent', 0, null).moment).toEqual({ cle: 'ruban.aucune_attente', heure: null })
  })

  it('affiche le compte exact au-delà de 99', () => {
    expect(deriverEtatRuban('bon', 150, dix_heures).titre).toEqual({ cle: 'ruban.envoi_de', params: { n: 150 } })
    expect(deriverEtatRuban('absent', 1000, null).moment.params).toEqual({ n: 1000 })
  })

  it('ne produit jamais de rouge, et ne connaît que les voix du composant', () => {
    const voix = new Set<string>()
    for (const reseau of ['bon', 'faible', 'absent'] as const) {
      for (const attente of [0, 1, 99, 100]) voix.add(deriverEtatRuban(reseau, attente, null).voix)
    }
    expect([...voix].sort()).toEqual([...COMPOSANTS.RubanSaisie.VOIX].sort())
    expect(voix.has('rouge')).toBe(false)
  })

  it('refuse un compte négatif ou non entier en le ramenant à zéro', () => {
    expect(deriverEtatRuban('bon', -3, null).etat).toBe('enregistre')
    expect(deriverEtatRuban('bon', Number.NaN, null).etat).toBe('enregistre')
  })
})
