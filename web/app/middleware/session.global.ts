// La garde de session (research.md R-10) : une page à coquille exige un contexte, donc une
// session. Sans contexte, elle n'est pas grisée ni vidée, elle n'est pas rendue : la personne
// est conduite vers la connexion.
//
// **Mais un contexte nul ne prouve rien au rendu du serveur.** Le cookie de rafraîchissement est
// borné à `/api/v1/auth` (data-model.md) : une requête de page ne le porte pas, et le serveur ne
// peut donc pas distinguer une session finie d'un jeton d'accès simplement expiré. Le client,
// lui, le peut : il demande un jeton neuf, puis relit le contexte (`app.vue`). La garde n'envoie
// vers la connexion qu'après cette tentative, et seulement si elle a échoué (FR-013).
//
// Les pages `sansCoquille` (la connexion elle-même, l'activation, la page de style) s'en
// passent : elles ne lisent aucun contexte.
import type { ContexteCapacites } from '~/core/contexte/types'

/** L'écran qui ouvre une session, atteignable sans session. */
export const CONNEXION = '/connexion'
/** Vrai dès que le client a tenté, une fois, de renouveler le jeton d'accès. */
export const CLE_REPRISE = 'session-reprise-tentee'

export default defineNuxtRouteMiddleware((vers) => {
  if (vers.meta.sansCoquille) return
  if (vers.path === CONNEXION) return
  const contexte = useState<ContexteCapacites | null>('contexte', () => null)
  if (contexte.value !== null) return
  // Au rendu du serveur, l'écran attend : c'est app.vue qui rend l'état d'attente, et le client
  // qui tranche. Rediriger ici priverait la personne d'une session qui vit encore.
  if (import.meta.server) return
  const tentee = useState<boolean>(CLE_REPRISE, () => false)
  if (!tentee.value) return
  return navigateTo(CONNEXION)
})
