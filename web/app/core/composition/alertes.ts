// Les alertes du contexte, présentées par le composant alerte (FR-028, composants.md § 11).
// La gravité commande le niveau ; le rouge reste réservé à deux types. Une action n'existe que
// si le domaine qu'elle ouvre est composé pour la personne : sinon elle est absente.
import type { NiveauAlerte } from '../composants/etats'
import type { AlerteContexte } from '../contexte/types'

const TYPES_ROUGES = new Set(['IMPAYE', 'ABSENCE_NON_JUSTIFIEE'])

const CONNUS: Record<string, { domaine: string | null }> = {
  BUDGET_SMS_BAS: { domaine: 'communication' },
}

export interface AlertePresentee {
  type: string
  niveau: NiveauAlerte
  titre: string
  corps: string | undefined
  parametres: Record<string, string | number>
  action: { libelle: string; vers: string } | null
}

function niveau(alerte: AlerteContexte): NiveauAlerte {
  switch (alerte.gravite) {
    case 'ALERTE':
      return 'attente'
    case 'CRITIQUE':
      return TYPES_ROUGES.has(alerte.type) ? 'danger' : 'attente'
    default:
      return 'information'
  }
}

export function presenterAlerte(alerte: AlerteContexte, domainesComposes: string[]): AlertePresentee {
  const connu = CONNUS[alerte.type]
  const racine = `alerte.type.${alerte.type}`
  const parametres = Object.fromEntries(
    Object.entries(alerte.details ?? {}).filter(
      (e): e is [string, string | number] => typeof e[1] === 'string' || typeof e[1] === 'number',
    ),
  )
  const domaine = connu?.domaine
  return {
    type: alerte.type,
    niveau: niveau(alerte),
    titre: connu ? `${racine}.titre` : 'alerte.type.inconnu.titre',
    corps: connu ? `${racine}.corps` : undefined,
    parametres,
    action:
      domaine && domainesComposes.includes(domaine)
        ? { libelle: `${racine}.action`, vers: `/d/${domaine}` }
        : null,
  }
}
