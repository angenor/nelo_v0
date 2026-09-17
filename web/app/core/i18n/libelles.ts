// Les libellés d'interface (research.md R-10). Deux dictionnaires plats, clés en notation
// pointée, valeurs fr et en nées ensemble (P-06, règle 2). Aucune bibliothèque d'i18n.
//
// Paramètres : « {n} » est remplacé par la valeur de params.n. Quand params.n vaut 1 et que la
// clé « <clé>.un » existe, c'est elle qui est employée : le seul pluriel dont la tranche a besoin.
// Une clé absente rend une chaîne vide, jamais la clé brute (FR-054) ; le rappel la signale.
import en from './en.json'
import fr from './fr.json'

export const LANGUES = ['fr', 'en'] as const
export type Langue = (typeof LANGUES)[number]
export type Dictionnaire = Record<string, string>
export type Parametres = Record<string, string | number>

export const DICTIONNAIRES: Record<Langue, Dictionnaire> = { fr, en }

export function estLangue(valeur: unknown): valeur is Langue {
  return LANGUES.includes(valeur as Langue)
}

export function traduire(
  dictionnaire: Dictionnaire,
  cle: string,
  params?: Parametres,
  signaler?: (cle: string) => void,
): string {
  const variante = params?.n === 1 ? dictionnaire[`${cle}.un`] : undefined
  const modele = variante ?? dictionnaire[cle]
  if (modele === undefined) {
    signaler?.(cle)
    return ''
  }
  if (!params) return modele
  return modele.replace(/\{([a-z_]+)\}/g, (entier, nom: string) =>
    nom in params ? String(params[nom]) : entier,
  )
}
