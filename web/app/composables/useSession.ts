// L'ouverture d'une session, vue du navigateur (research.md R-09, R-21) : deux appels, et ce
// qu'il faut retenir entre l'écran du numéro et celui du code.
//
// Aucun jeton ne passe ici. Le relais de Nitro range le jeton d'accès dans un cookie que nul
// script ne lit, et le rafraîchissement vit dans un autre cookie : ce composable ne connaît que
// le numéro que la personne a saisi et l'instant de la dernière demande.
import type { ClientApi } from '~/core/api/client'
import { ErreurApi, RAFRAICHISSEMENT } from '~/core/api/client'
import type { CompteConnu, Etape, ReponseVerification, SessionOuverte } from '~/core/session/etat'
import { DELAI_RENVOI, etapeSuivante, REFUS } from '~/core/session/etat'

const DEMANDE = '/auth/otp'
const VERIFICATION = '/auth/otp/verification'
const APPAREIL = '/auth/appareil'
const PIN = '/auth/pin'
const DEFINITION_PIN = '/auth/pin/definition'
const INVITATION = '/auth/invitation'
const FERMETURE = '/auth/session'
const TELEPHONE = '/moi/telephone'
const VERIFICATION_TELEPHONE = '/moi/telephone/verification'

/** Les secondes de reprise que porte un refus de débit, quand il en porte. */
function repriseDans(details: Record<string, unknown>): number {
  const secondes = details.reprise_dans
  return typeof secondes === 'number' && secondes > 0 ? secondes : DELAI_RENVOI
}

export function useSession() {
  const api: ClientApi = useApi()
  /** Le numéro tel qu'il part vers le serveur : l'écran du code l'affiche et le rejoue. */
  const identifiant = useState<string>('session-identifiant', () => '')
  /** L'instant de la dernière demande, en millisecondes ; zéro quand aucune n'a été faite. */
  const demandeLe = useState<number>('session-demande-le', () => 0)
  /** Les secondes à attendre avant un renvoi : soixante, ou ce que le refus de débit a dit. */
  const delaiRenvoi = useState<number>('session-delai-renvoi', () => DELAI_RENVOI)

  /**
   * Demande un code. La réponse est la même pour tout numéro bien formé : rien n'y dit si un
   * compte le porte. Un refus de débit n'est pas une panne, c'est une attente : il est noté,
   * puis remonté tel quel à l'écran, qui en dit la durée.
   */
  async function demanderCode(numero: string): Promise<void> {
    identifiant.value = numero
    try {
      await api.appeler<void>('POST', DEMANDE, { corps: { identifiant: numero }, ecriture: true })
      demandeLe.value = Date.now()
      delaiRenvoi.value = DELAI_RENVOI
    } catch (echec) {
      if (echec instanceof ErreurApi && echec.code === REFUS.limiteDebit) {
        demandeLe.value = Date.now()
        delaiRenvoi.value = repriseDans(echec.details)
      }
      throw echec
    }
  }

  /**
   * Échange le code contre une session. La réponse dit elle-même la suite : une session ouverte,
   * ou le choix du compte quand le numéro en porte plusieurs (US8).
   */
  async function verifierCode(numero: string, code: string, compteId?: string): Promise<Etape> {
    const corps: Record<string, string> = { identifiant: numero, code }
    if (compteId) corps.compte_id = compteId
    const reponse = await api.appeler<ReponseVerification>('POST', VERIFICATION, {
      corps,
      ecriture: true,
    })
    return etapeSuivante(reponse)
  }

  /**
   * Demande un jeton d'accès neuf. **Depuis le navigateur seulement** : le cookie de
   * rafraîchissement est borné au chemin de l'authentification, il accompagne cet appel et
   * aucun autre, jamais une requête de page (research.md R-09, data-model.md).
   *
   * Un refus n'est pas une panne : c'est la réponse « cette session est finie », et l'appelant
   * conduit alors vers l'écran de connexion.
   */
  async function renouveler(): Promise<boolean> {
    try {
      await api.appeler<unknown>('POST', RAFRAICHISSEMENT, { ecriture: true })
      return true
    } catch (echec) {
      if (!(echec instanceof ErreurApi)) throw echec
      return false
    }
  }

  /**
   * Les comptes que cet appareil connaît (research.md R-20) : un nom, jamais un numéro. La
   * réponse est vide quand l'appareil n'est connu d'aucun compte, et c'est alors le parcours
   * par code reçu qui s'affiche.
   */
  async function comptesDeLAppareil(): Promise<CompteConnu[]> {
    const reponse = await api.appeler<{ comptes: CompteConnu[] }>('GET', APPAREIL)
    return reponse.comptes
  }

  /** Ouvre une session par code personnel, sur un appareil que le compte connaît. */
  function ouvrirParPin(compteId: string, pin: string): Promise<SessionOuverte> {
    return api.appeler<SessionOuverte>('POST', PIN, {
      corps: { compte_id: compteId, pin },
      ecriture: true,
    })
  }

  /**
   * Définit ou change le code personnel. Le code courant n'accompagne la demande que si la
   * personne en a un : dans les dix minutes qui suivent une ouverture par code reçu ou par
   * lien, le serveur en dispense, et c'est le seul cas.
   */
  function definirPin(pin: string, pinCourant?: string): Promise<void> {
    const corps: Record<string, string> = { pin }
    if (pinCourant) corps.pin_courant = pinCourant
    return api.appeler<void>('POST', DEFINITION_PIN, { corps, ecriture: true })
  }

  /** Active un compte depuis son lien à usage unique : la session s'ouvre, l'appareil devient connu. */
  function activerParInvitation(jeton: string): Promise<SessionOuverte> {
    return api.appeler<SessionOuverte>('POST', `${INVITATION}/${encodeURIComponent(jeton)}`, {
      ecriture: true,
    })
  }

  /**
   * Ferme la session. Les jetons sont révoqués sur-le-champ et le relais efface son cookie ;
   * l'appareil, lui, reste connu : la prochaine ouverture se fait par code personnel. Un refus
   * ne retient personne : la session est finie de toute façon, et l'écran de connexion suit.
   */
  async function fermer(): Promise<void> {
    try {
      await api.appeler<void>('DELETE', FERMETURE, { ecriture: true })
    } catch (echec) {
      if (!(echec instanceof ErreurApi)) throw echec
    } finally {
      identifiant.value = ''
      demandeLe.value = 0
      delaiRenvoi.value = DELAI_RENVOI
    }
  }

  /** Demande le changement de son numéro : le code part vers le **nouveau** numéro. */
  async function demanderChangementTelephone(nouveau: string): Promise<void> {
    try {
      await api.appeler<void>('POST', TELEPHONE, {
        corps: { nouvel_identifiant: nouveau },
        ecriture: true,
      })
      demandeLe.value = Date.now()
      delaiRenvoi.value = DELAI_RENVOI
    } catch (echec) {
      if (echec instanceof ErreurApi && echec.code === REFUS.limiteDebit) {
        demandeLe.value = Date.now()
        delaiRenvoi.value = repriseDans(echec.details)
      }
      throw echec
    }
  }

  /** Vérifie le code reçu sur le nouveau numéro : c'est là que l'identifiant change. */
  function verifierChangementTelephone(code: string): Promise<void> {
    return api.appeler<void>('POST', VERIFICATION_TELEPHONE, { corps: { code }, ecriture: true })
  }

  return {
    identifiant,
    demandeLe,
    delaiRenvoi,
    demanderCode,
    verifierCode,
    renouveler,
    comptesDeLAppareil,
    ouvrirParPin,
    definirPin,
    activerParInvitation,
    fermer,
    demanderChangementTelephone,
    verifierChangementTelephone,
  }
}
