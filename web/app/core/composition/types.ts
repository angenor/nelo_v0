// Les formes dérivées du contexte (data-model.md § 2, contracts § 4). Aucune ne porte de rôle,
// aucune n'a de champ « désactivé » : un domaine sans capacité n'existe pas.
import type { Situation } from '../composants/etats'

export type CodeFamille = 'ELEVES' | 'ENSEIGNEMENT' | 'GESTION' | 'COMMUNICATION' | 'PARAMETRES'

export type IconeDomaine =
  | 'inscription'
  | 'appel'
  | 'horloge'
  | 'sanction'
  | 'progression'
  | 'evaluation'
  | 'conseil'
  | 'finance'
  | 'personnel'
  | 'message'
  | 'reglage'

/** Une clé d'interface, ou un code neutre du pack quand le mot est métier. */
export type Libelle = { cle: string } | { code: string }

export interface Famille {
  code: CodeFamille
  libelleCle: string
  ordre: number
}

/** Un écran d'un domaine, que la navigation mono-domaine liste à plat (FR-023). */
export interface Entree {
  code: string
  libelle: Libelle
  route: string
  icone: IconeDomaine
  /** Ce que le contexte porte pour cette entrée ; jamais calculé par le client (FR-027). */
  compte: number | null
}

export interface Domaine {
  code: string
  libelle: Libelle
  famille: CodeFamille
  ordre: number
  route: string
  icone: IconeDomaine
  /** Ce que le contexte porte pour ce domaine ; jamais calculé par le client (FR-027). */
  compte: number | null
  /** Les écrans du domaine que les capacités de la personne ouvrent, dans l'ordre du registre. */
  entrees: Entree[]
}

export interface Composition {
  situation: Situation
  domaines: Domaine[]
  familles: { famille: Famille; domaines: Domaine[] }[]
  accueil: { route: string }
}
