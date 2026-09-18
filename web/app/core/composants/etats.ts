// Les états des quatorze composants canoniques, en un seul endroit (FR-092, research.md R-03).
// docs/design/composants.md les décrit, chaque composant les réexporte, la page de style les
// itère, et un test vérifie que les trois disent la même chose.

export const COMPOSANTS = {
  Bouton: {
    VARIANTES: ['principal', 'secondaire', 'discret', 'danger'],
    ETATS: ['repos', 'focus', 'presse', 'inactif'],
  },
  Champ: {
    TYPES: ['texte', 'nombre', 'choix', 'case'],
    SAISIES: ['texte', 'code'],
    ETATS: ['repos', 'focus', 'erreur', 'inactif'],
    COMPLEMENTS: ['aide', 'unite'],
  },
  Interrupteur: {
    ETATS: ['active', 'desactive', 'inactif'],
  },
  PastilleEtat: {
    VOIX: ['reussite', 'ocre', 'rouge', 'neutre', 'contour'],
    FORMES: ['rond', 'capsule'],
  },
  PastilleCanal: {
    CANAUX: ['EN_LIGNE', 'WHATSAPP', 'SMS', 'PAPIER'],
    COUTS: ['sans_cout', 'avec_cout'],
  },
  Recherche: {
    ETATS: ['repos', 'focus', 'saisie', 'resultats', 'aucun'],
    CONTEXTES: ['mobile', 'poste'],
  },
  Avatar: {
    TAILLES: ['petite', 'grande'],
    SOURCES: ['initiales', 'photo'],
  },
  FilAriane: {
    SEGMENTS: ['lien', 'courant'],
  },
  Onglets: {
    ETATS: ['actif', 'inactif', 'avec_compte'],
  },
  CarteIndicateur: {
    SENS: ['positive', 'negative', 'neutre'],
    VALEURS: ['ordinaire', 'reservee'],
  },
  Alerte: {
    NIVEAUX: ['information', 'attente', 'danger', 'enregistre'],
    ACTIONS: ['sans_action', 'avec_action'],
  },
  Tableau: {
    MODES: ['lignes', 'cartes'],
    CELLULES: ['texte', 'mono', 'pastille', 'canal'],
  },
  RubanSaisie: {
    ETATS: ['enregistre', 'envoi', 'hors_ligne'],
    VOIX: ['reussite', 'marque', 'ocre'],
  },
  Coquille: {
    SITUATIONS: ['AUCUNE_CAPACITE', 'MONO_DOMAINE', 'MULTI_PLAT', 'MULTI_FAMILLES'],
  },
} as const

type Valeur<C extends keyof typeof COMPOSANTS, E extends keyof (typeof COMPOSANTS)[C]> =
  (typeof COMPOSANTS)[C][E] extends readonly (infer V)[] ? V : never

export type VarianteBouton = Valeur<'Bouton', 'VARIANTES'>
export type EtatBouton = Valeur<'Bouton', 'ETATS'>
export type TypeChamp = Valeur<'Champ', 'TYPES'>
export type SaisieChamp = Valeur<'Champ', 'SAISIES'>
export type EtatChamp = Valeur<'Champ', 'ETATS'>
export type VoixPastille = Valeur<'PastilleEtat', 'VOIX'>
export type FormePastille = Valeur<'PastilleEtat', 'FORMES'>
export type Canal = Valeur<'PastilleCanal', 'CANAUX'>
export type EtatRecherche = Valeur<'Recherche', 'ETATS'>
export type TailleAvatar = Valeur<'Avatar', 'TAILLES'>
export type SensVariation = Valeur<'CarteIndicateur', 'SENS'>
export type NiveauAlerte = Valeur<'Alerte', 'NIVEAUX'>
export type EtatRuban = Valeur<'RubanSaisie', 'ETATS'>
export type VoixRuban = Valeur<'RubanSaisie', 'VOIX'>
export type Situation = Valeur<'Coquille', 'SITUATIONS'>

/**
 * Les états métier qu'une pastille sait dire, avec leur voix et leur mot. La voix ne se choisit
 * pas à l'appel : elle se déduit du code, et seuls IMPAYE et NON_JUSTIFIE parlent en rouge
 * (FR-005). « Validé » prend la voix de réussite (research.md R-19).
 */
export const ETATS_METIER = {
  PAYE: { voix: 'reussite', cle: 'etat.paye' },
  SOLDE: { voix: 'reussite', cle: 'etat.solde' },
  JUSTIFIE: { voix: 'reussite', cle: 'etat.justifie' },
  ENREGISTRE: { voix: 'reussite', cle: 'etat.enregistre' },
  VALIDE: { voix: 'reussite', cle: 'etat.valide' },
  ECHEANCE_PROCHE: { voix: 'ocre', cle: 'etat.echeance_proche' },
  EN_ATTENTE: { voix: 'ocre', cle: 'etat.en_attente' },
  NON_FAIT: { voix: 'ocre', cle: 'etat.non_fait' },
  IMPAYE: { voix: 'rouge', cle: 'etat.impaye' },
  NON_JUSTIFIE: { voix: 'rouge', cle: 'etat.non_justifie' },
  PRESENT: { voix: 'neutre', cle: 'etat.present' },
  BROUILLON: { voix: 'neutre', cle: 'etat.brouillon' },
  PROPOSE: { voix: 'contour', cle: 'etat.propose' },
  // L'année de travail (écart E-03 de T1a) : une année en préparation n'est pas une faute,
  // c'est une attente, et l'année active ne parle d'aucune réussite.
  ANNEE_ACTIVE: { voix: 'neutre', cle: 'etat.annee_active' },
  ANNEE_PREPARATION: { voix: 'ocre', cle: 'etat.annee_preparation' },
} as const satisfies Record<string, { voix: VoixPastille; cle: string }>

export type CodeEtat = keyof typeof ETATS_METIER

/** Le contexte tactile d'un écran : la hauteur de ses cibles (contracts § 2). */
export const CONTEXTES_TACTILES = ['classe', 'standard', 'poste'] as const
export type ContexteTactile = (typeof CONTEXTES_TACTILES)[number]
