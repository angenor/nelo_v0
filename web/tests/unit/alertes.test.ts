// FR-028 : une alerte du contexte prend le niveau que sa gravité commande ; le danger reste
// réservé à l'impayé et à l'absence non justifiée.
import { describe, expect, it } from 'vitest'
import { presenterAlerte } from '../../app/core/composition/alertes'

const alerte = (type: string, gravite: string, details = {}) => ({ type, gravite, details }) as never

describe('presenterAlerte', () => {
  it('INFO en information, ALERTE en attente', () => {
    expect(presenterAlerte(alerte('BUDGET_SMS_BAS', 'INFO'), []).niveau).toBe('information')
    expect(presenterAlerte(alerte('BUDGET_SMS_BAS', 'ALERTE'), []).niveau).toBe('attente')
  })

  it('CRITIQUE en danger seulement pour un impayé ou une absence non justifiée', () => {
    expect(presenterAlerte(alerte('IMPAYE', 'CRITIQUE'), []).niveau).toBe('danger')
    expect(presenterAlerte(alerte('ABSENCE_NON_JUSTIFIEE', 'CRITIQUE'), []).niveau).toBe('danger')
    expect(presenterAlerte(alerte('BUDGET_SMS_BAS', 'CRITIQUE'), []).niveau).toBe('attente')
  })

  it('une gravité inconnue est une information', () => {
    expect(presenterAlerte(alerte('BUDGET_SMS_BAS', 'AUTRE'), []).niveau).toBe('information')
  })

  it('un type connu a ses clés et ses paramètres, un type inconnu une clé générique', () => {
    const connue = presenterAlerte(alerte('BUDGET_SMS_BAS', 'ALERTE', { restant: 1240 }), ['communication'])
    expect(connue).toMatchObject({
      titre: 'alerte.type.BUDGET_SMS_BAS.titre',
      corps: 'alerte.type.BUDGET_SMS_BAS.corps',
      parametres: { restant: 1240 },
    })
    expect(presenterAlerte(alerte('NOUVEAU_TYPE', 'INFO'), []).titre).toBe('alerte.type.inconnu.titre')
  })

  it('n’offre une action que si le domaine qu’elle ouvre est composé', () => {
    const avec = presenterAlerte(alerte('BUDGET_SMS_BAS', 'ALERTE'), ['communication'])
    expect(avec.action).toEqual({ libelle: 'alerte.type.BUDGET_SMS_BAS.action', vers: '/d/communication' })
    expect(presenterAlerte(alerte('BUDGET_SMS_BAS', 'ALERTE'), ['finance']).action).toBeNull()
  })
})
