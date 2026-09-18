// Le relais (research.md R-09) : toute requête `/api/v1/**` du navigateur passe par ici avant
// d'atteindre l'API. C'est la seule brique du dépôt qui connaît un cookie de jeton.
//
// Il fait quatre choses, et aucune règle métier :
//   1. il transforme le cookie `nelo_acces` en `Authorization: Bearer` vers l'API ;
//   2. il pose `X-Forwarded-For`, sans quoi la limitation par client verrait une seule adresse ;
//   3. il transmet tels quels les `Set-Cookie` de l'API (`nelo_refresh`, `nelo_appareils`) ;
//   4. sur une réponse qui porte `jeton_acces`, il range le jeton dans `nelo_acces`
//      (`HttpOnly`, donc hors de portée de tout script) et le retire du corps ; sur la fermeture
//      de session, il efface ce cookie.
//
// Aucun jeton n'est donc jamais visible d'un script, ni en stockage, ni en mémoire de page.
import type { H3Event } from 'h3'
import {
  defineEventHandler,
  deleteCookie,
  getCookie,
  getRequestHeader,
  getRequestIP,
  proxyRequest,
  send,
  setCookie,
} from 'h3'

/** Le jeton d'accès, posé et lu par le seul relais. */
const COOKIE_ACCES = 'nelo_acces'
/** La fermeture de session, la seule requête qui efface le cookie sans réponse à réécrire. */
const FERMETURE = '/api/v1/auth/session'

interface CorpsAvecJeton {
  jeton_acces?: unknown
  expire_dans?: unknown
}

function estJson(reponse: Response): boolean {
  return (reponse.headers.get('content-type') ?? '').includes('json')
}

/** L'adresse du demandeur, ajoutée à la chaîne que l'API lira (NELO_RELAIS_DE_CONFIANCE). */
function chaineTransmise(evenement: H3Event): string | undefined {
  const amont = getRequestHeader(evenement, 'x-forwarded-for')
  const adresse = getRequestIP(evenement)
  const chaine = [amont, adresse].filter(Boolean).join(', ')
  return chaine === '' ? undefined : chaine
}

function rangerJeton(evenement: H3Event, corps: CorpsAvecJeton, secure: boolean): void {
  const duree = typeof corps.expire_dans === 'number' ? corps.expire_dans : undefined
  setCookie(evenement, COOKIE_ACCES, String(corps.jeton_acces), {
    httpOnly: true,
    secure,
    sameSite: 'strict',
    path: '/',
    maxAge: duree,
  })
  delete corps.jeton_acces
}

export default defineEventHandler(async (evenement) => {
  const configuration = useRuntimeConfig(evenement)
  const jeton = getCookie(evenement, COOKIE_ACCES)
  const entetes: Record<string, string> = {}
  if (jeton) entetes.authorization = `Bearer ${jeton}`
  const transmise = chaineTransmise(evenement)
  if (transmise) entetes['x-forwarded-for'] = transmise

  return await proxyRequest(evenement, `${configuration.apiBase}${evenement.path}`, {
    headers: entetes,
    async onResponse(evenementProxy, reponse) {
      const reussie = reponse.status >= 200 && reponse.status < 300
      if (reussie && evenementProxy.method === 'DELETE' && evenementProxy.path === FERMETURE) {
        deleteCookie(evenementProxy, COOKIE_ACCES, { path: '/' })
      }
      if (!estJson(reponse)) return
      // Lire le corps le consomme : c'est donc le relais qui l'envoie, réécrit ou tel quel.
      const texte = await reponse.text()
      let corps: CorpsAvecJeton | null = null
      try {
        corps = JSON.parse(texte) as CorpsAvecJeton
      } catch {
        corps = null
      }
      if (corps === null || corps.jeton_acces === undefined) {
        await send(evenementProxy, texte)
        return
      }
      rangerJeton(evenementProxy, corps, configuration.cookiesSecure)
      await send(evenementProxy, JSON.stringify(corps))
    },
  })
})
