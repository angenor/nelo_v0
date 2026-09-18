// Ce que les écrans de la session montrent, une fois la réponse du serveur traduite
// (research.md R-21), en fonctions pures. Rien ici n'appelle le réseau, rien n'y garde de jeton,
// et aucune règle métier n'y est rejouée : le serveur juge, ces fonctions traduisent.
//
// Ce module vit à part du socle de la session (`etat.ts`) pour une raison de poids : la coquille
// a besoin du socle sur **chaque** écran, alors que ces fonctions ne servent qu'aux cinq écrans
// de la session. Les séparer les tient hors du premier affichage de tous les autres (P-10).
import type { NiveauAlerte } from '../composants/etats'
import { LONGUEUR_CODE, LONGUEUR_PIN, REFUS } from './etat'

/** Ce que l'écran du numéro tient : la forme est de présentation, le serveur reste seul juge. */
export interface EcranNumero {
  /** La clé de l'erreur portée par le champ, ou rien. */
  erreur: string | null
}

/** Des chiffres et leurs séparateurs d'usage, rien d'autre ; le serveur normalise le reste. */
const CHIFFRES_ET_SEPARATEURS = /^[+\d\s.-]*$/
const CHIFFRES = /\d/g

/** Le nombre de chiffres saisis, séparateurs retirés. */
export function chiffres(saisie: string): number {
  return (saisie.match(CHIFFRES) ?? []).length
}

/**
 * Une forme plausible de numéro : au moins six chiffres, et aucun caractère qui n'a rien à faire
 * dans un numéro. Ce n'est pas la validation, qui appartient au serveur (FR-002) : c'est ce qui
 * évite d'envoyer un message court pour une saisie manifestement inachevée.
 */
export function formePlausible(saisie: string): boolean {
  return CHIFFRES_ET_SEPARATEURS.test(saisie) && chiffres(saisie) >= 6
}

/**
 * L'écran du numéro. Le refus de forme ne s'affiche pas dès la première touche : il attend soit
 * un caractère impossible, soit une tentative d'envoi. Avant cela, l'aide dit déjà ce qu'on
 * attend, et c'est la règle « le refus s'annonce avant la saisie ».
 */
export function etatEcranNumero(entree: {
  saisie: string
  tentee: boolean
  refus: string | null
}): EcranNumero {
  if (entree.refus === REFUS.numeroInvalide) return { erreur: 'session.numero.format' }
  const impossible = entree.saisie !== '' && !CHIFFRES_ET_SEPARATEURS.test(entree.saisie)
  if (impossible || (entree.tentee && !formePlausible(entree.saisie))) {
    return { erreur: 'session.numero.format' }
  }
  return { erreur: null }
}

/**
 * L'identifiant envoyé : l'indicatif affiché, puis les chiffres saisis, tels qu'ils se lisent.
 * La personne qui écrit elle-même un indicatif international garde le sien. Le serveur normalise
 * l'écriture, quelle qu'elle soit : ici on assemble ce que l'écran montre, rien de plus.
 */
export function identifiant(indicatif: string, saisie: string): string {
  const propre = saisie.trim()
  if (propre.startsWith('+') || indicatif === '') return propre
  return `${indicatif} ${propre}`
}

/** Ce que l'écran du code montre, une fois le refus du serveur traduit. */
export interface EcranCode {
  /** Le champ des six chiffres : absent tant qu'aucun code vivant n'existe, jamais grisé. */
  champ: boolean
  /** La clé de l'erreur du champ, et ses paramètres. */
  erreur: string | null
  parametresErreur: Record<string, number> | undefined
  /** L'alerte au-dessus du champ : son niveau et ses clés. */
  alerte: { niveau: NiveauAlerte; titre: string; corps: string } | null
  /** L'action principale : ouvrir la session, ou demander un code neuf. */
  action: 'ouvrir' | 'nouveau'
  /** Le compte à rebours du renvoi, en secondes ; zéro quand le renvoi est ouvert. */
  secondes: number
}

export interface EntreeEcranCode {
  /** Le code saisi, tel quel. */
  saisie: string
  /** Une vérification a été tentée avec une saisie qui n'a pas six chiffres. */
  tentee: boolean
  /** Le code du refus rendu par le serveur, ou rien. */
  refus: string | null
  /** `details.tentatives_restantes` du refus `AUT_OTP_INVALIDE`. */
  tentativesRestantes: number | null
  /** Les secondes qui restent avant le renvoi. */
  secondes: number
}

/**
 * L'état de l'écran du code. Chaque refus porte son versant positif : un code faux dit ce qui
 * reste, un code mort propose d'en recevoir un neuf, une limite de débit dit sa durée et rappelle
 * que le dernier code vaut toujours. Un code détruit fait disparaître le champ, il ne le grise
 * pas. Un refus que cet écran ne connaît pas ne parle pas à sa place : US5 les nomme.
 */
export function etatEcranCode(entree: EntreeEcranCode): EcranCode {
  const base: EcranCode = {
    champ: true,
    erreur: null,
    parametresErreur: undefined,
    alerte: null,
    action: 'ouvrir',
    secondes: entree.secondes,
  }
  if (entree.refus === REFUS.codeFaux) {
    return {
      ...base,
      erreur: 'session.code.tentatives_restantes',
      parametresErreur: { n: entree.tentativesRestantes ?? 0 },
    }
  }
  if (entree.refus === REFUS.codeExpire) {
    return {
      ...base,
      champ: false,
      action: 'nouveau',
      alerte: { niveau: 'information', titre: 'session.code.expire', corps: 'session.code.expire_corps' },
    }
  }
  if (entree.refus === REFUS.codeEpuise) {
    return {
      ...base,
      champ: false,
      action: 'nouveau',
      alerte: { niveau: 'information', titre: 'session.code.epuise', corps: 'session.code.epuise_corps' },
    }
  }
  if (entree.refus === REFUS.limiteDebit) {
    return {
      ...base,
      alerte: {
        niveau: 'attente',
        titre: 'session.code.trop_de_demandes',
        corps: 'session.code.trop_de_demandes_corps',
      },
    }
  }
  if (entree.tentee && entree.saisie.length !== LONGUEUR_CODE) {
    return { ...base, erreur: 'session.code.format' }
  }
  return base
}


/** Quatre chiffres, rien d'autre : la forme que le serveur exige (`^\\d{4}$`). */
const QUATRE_CHIFFRES = /^\d{4}$/

export function formePin(saisie: string): boolean {
  return QUATRE_CHIFFRES.test(saisie)
}

/** Ce que l'écran de définition du code personnel montre (US3, artboard US3). */
export interface EcranPin {
  /** La clé de l'erreur du premier champ, ou rien. */
  erreur: string | null
  /** La clé de l'erreur du second champ : la confirmation. */
  erreurConfirmation: string | null
}

/**
 * L'écran qui définit le code personnel. Le refus de format s'annonce pendant la saisie, dès
 * qu'un caractère qui n'est pas un chiffre apparaît ; la différence entre les deux codes, elle,
 * attend que le second soit complet : le dire au premier chiffre serait dire une faute avant
 * qu'elle existe.
 */
export function etatEcranPin(entree: {
  pin: string
  confirmation: string
  tentee: boolean
  refus: string | null
}): EcranPin {
  const chiffresSeuls = /^\d*$/
  const formeFausse = !chiffresSeuls.test(entree.pin) || (entree.tentee && !formePin(entree.pin))
  if (formeFausse) return { erreur: 'session.pin.format', erreurConfirmation: null }
  if (entree.refus === REFUS.pinFaux || entree.refus === REFUS.pinAbsent) {
    return { erreur: 'session.pin.courant_faux', erreurConfirmation: null }
  }
  const comparable = entree.tentee || entree.confirmation.length >= LONGUEUR_PIN
  if (comparable && entree.confirmation !== entree.pin) {
    return { erreur: null, erreurConfirmation: 'session.pin.differents' }
  }
  return { erreur: null, erreurConfirmation: null }
}

/** Ce que l'écran d'ouverture par code personnel montre, une fois le refus traduit. */
export interface EcranOuverture {
  /** Le champ des quatre chiffres : absent quand le code personnel ne peut plus servir. */
  champ: boolean
  erreur: string | null
  parametresErreur: Record<string, number> | undefined
  alerte: { niveau: NiveauAlerte; titre: string; corps: string } | null
  /** Vrai quand l'appareil doit oublier ce compte : le parcours par code reçu le remplace. */
  oublier: boolean
}

/**
 * L'écran d'ouverture par code personnel (US3, scénarios 2, 4 et 8). Un code faux dit ce qui
 * reste ; un code verrouillé fait **disparaître** le champ et laisse le SMS pour seule issue ;
 * un compte suspendu dit ce qui reste ouvert, et l'appareil l'oublie.
 */
export function etatEcranOuverture(entree: {
  refus: string | null
  tentativesRestantes: number | null
}): EcranOuverture {
  const base: EcranOuverture = {
    champ: true,
    erreur: null,
    parametresErreur: undefined,
    alerte: null,
    oublier: false,
  }
  if (entree.refus === REFUS.pinFaux) {
    return {
      ...base,
      erreur: 'session.ouverture.faux',
      parametresErreur: { n: entree.tentativesRestantes ?? 0 },
    }
  }
  if (entree.refus === REFUS.pinEpuise) {
    return {
      ...base,
      champ: false,
      alerte: {
        niveau: 'information',
        titre: 'session.ouverture.verrou',
        corps: 'session.ouverture.verrou_corps',
      },
    }
  }
  if (entree.refus === REFUS.compteSuspendu) {
    return {
      ...base,
      champ: false,
      oublier: true,
      alerte: {
        niveau: 'information',
        titre: 'session.suspendu.titre',
        corps: 'session.suspendu.corps',
      },
    }
  }
  if (entree.refus === REFUS.appareilInconnu || entree.refus === REFUS.pinAbsent) {
    return {
      ...base,
      champ: false,
      oublier: true,
      alerte: {
        niveau: 'information',
        titre: 'session.ouverture.inconnu',
        corps: 'session.ouverture.inconnu_corps',
      },
    }
  }
  return base
}
