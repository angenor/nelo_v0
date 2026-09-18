// L'état des deux écrans qui ouvrent une session (research.md R-21), en fonctions pures : ce que
// la réponse du serveur commande à l'écran, ce qu'un refus y montre, et le compte à rebours du
// renvoi. Rien ici n'appelle le réseau, rien n'y garde de jeton, et aucune règle métier n'y est
// rejouée : le serveur juge, ces fonctions traduisent sa réponse en choses à afficher.
import type { components } from '../../../../contrat/client'

export type ReponseVerification = components['schemas']['ReponseVerificationCode']
export type SessionOuverte = components['schemas']['SessionOuverte']
export type ChoixRequis = components['schemas']['ChoixRequis']
export type ChoixCompte = components['schemas']['ChoixCompte']
export type CompteConnu = components['schemas']['CompteConnu']

/** Les six chiffres du code reçu, et les secondes entre deux demandes (politique du serveur). */
export const LONGUEUR_CODE = 6
export const DELAI_RENVOI = 60
/** Les quatre chiffres du code personnel (02-domaine.md § 3.1, `CorpsOuverturePin`). */
export const LONGUEUR_PIN = 4

/** Les refus que les écrans savent dire ; les autres restent au serveur (US5 les nomme). */
export const REFUS = {
  numeroInvalide: 'AUT_NUMERO_INVALIDE',
  codeFaux: 'AUT_OTP_INVALIDE',
  codeExpire: 'AUT_OTP_EXPIRE',
  codeEpuise: 'AUT_OTP_TENTATIVES_EPUISEES',
  limiteDebit: 'API_LIMITE_DEBIT',
  appareilInconnu: 'AUT_APPAREIL_INCONNU',
  pinAbsent: 'AUT_PIN_ABSENT',
  pinFaux: 'AUT_PIN_INVALIDE',
  pinEpuise: 'AUT_PIN_TENTATIVES_EPUISEES',
  compteSuspendu: 'AUT_COMPTE_SUSPENDU',
  invitationInvalide: 'AUT_INVITATION_INVALIDE',
  identifiantPris: 'AUT_IDENTIFIANT_DEJA_UTILISE',
  sessionRevoquee: 'AUT_SESSION_REVOQUEE',
} as const

/**
 * Les motifs qu'une session finie porte à l'écran de connexion, en clair dans l'adresse
 * (`/connexion?motif=…`). Ils ne disent rien qu'un refus du serveur n'ait déjà dit : ils
 * choisissent le mot d'écran qui accueille la personne (FR-064, écart E-07).
 */
export const MOTIFS = ['revoquee', 'suspendu'] as const
export type Motif = (typeof MOTIFS)[number]

export function estMotif(valeur: unknown): valeur is Motif {
  return MOTIFS.includes(valeur as Motif)
}

/**
 * La suite du parcours, telle que la réponse la dicte. `resultat` la porte : le client ne devine
 * pas. Le choix de la personne appartient à US8 ; l'étape existe pour qu'il s'y branche.
 */
export type Etape =
  | { nom: 'session'; session: SessionOuverte }
  | { nom: 'choix'; comptes: ChoixRequis['comptes'] }

export function etapeSuivante(reponse: ReponseVerification): Etape {
  if (reponse.resultat === 'CHOIX') return { nom: 'choix', comptes: reponse.comptes }
  return { nom: 'session', session: reponse }
}

/**
 * Les secondes qui restent avant que le renvoi soit possible : jamais négatives, arrondies au
 * haut pour que « 1 s » s'affiche tant que la seconde court. `depuis` et `maintenant` sont des
 * millisecondes, `delai` des secondes.
 */
export function compteARebours(depuis: number, delai: number, maintenant: number = Date.now()): number {
  const restant = depuis + delai * 1000 - maintenant
  return restant <= 0 ? 0 : Math.ceil(restant / 1000)
}
