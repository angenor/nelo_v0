// Le pack de pays vu par l'interface (research.md R-10, contracts § 6). Il résout les codes
// neutres et met en forme ce que le serveur a calculé : aucun calcul, seulement de l'écriture.
// Les séparateurs dépendent de la langue, le symbole et l'exposant de la devise du pack ;
// aucun pays n'est nommé ici.
import type { CountryPackContexte } from '../contexte/types'

/** L'espace fine insécable des montants, que la revue visuelle a exigée partout. */
export const ESPACE_FINE = ' '

const SEPARATEURS: Record<string, { groupe: string; decimale: string }> = {
  fr: { groupe: ESPACE_FINE, decimale: ',' },
  en: { groupe: ',', decimale: '.' },
}

const DECIMAL = /^(-?)(\d+)(?:\.(\d+))?$/

function separateurs(langue: string) {
  return SEPARATEURS[langue] ?? SEPARATEURS.fr!
}

function grouper(chiffres: string, groupe: string): string {
  return chiffres.replace(/\B(?=(\d{3})+(?!\d))/g, groupe)
}

function majusculeInitiale(texte: string): string {
  return texte.charAt(0).toLocaleUpperCase() + texte.slice(1)
}

export interface Pack {
  langue: string
  devise: CountryPackContexte['devise']
  libelle(code: string): string
  montant(entier: number, options?: { symbole: boolean }): string
  decimal(valeur: string): string
  note(valeur: string, bareme: string): string
  date(iso: string): string
  jourMois(iso: string): string
  heure(instant: Date): string
}

export function creerPack(pack: CountryPackContexte, langueDemandee: string): Pack {
  const langue = pack.langues.includes(langueDemandee) ? langueDemandee : pack.langues[0]!
  const { groupe, decimale } = separateurs(langue)

  function decimal(valeur: string): string {
    const morceaux = DECIMAL.exec(valeur.trim())
    if (!morceaux) return ''
    const [, signe, entiere, fraction] = morceaux
    return `${signe}${grouper(entiere!, groupe)}${fraction ? decimale + fraction : ''}`
  }

  return {
    langue,
    devise: pack.devise,
    libelle(code) {
      const libelles = pack.vocabulaire[code]
      return libelles?.[langue] ?? libelles?.[pack.langues[0]!] ?? ''
    },
    decimal,
    montant(entier, options = { symbole: true }) {
      if (!Number.isSafeInteger(entier)) return ''
      const exposant = pack.devise.exposant
      const chiffres = Math.abs(entier)
        .toString()
        .padStart(exposant + 1, '0')
      const coupure = chiffres.length - exposant
      const texte = exposant > 0 ? `${chiffres.slice(0, coupure)}.${chiffres.slice(coupure)}` : chiffres
      const nombre = `${entier < 0 ? '-' : ''}${decimal(texte)}`
      return options.symbole ? `${nombre}${ESPACE_FINE}${pack.devise.symbole}` : nombre
    },
    note(valeur, bareme) {
      const v = decimal(valeur)
      const b = decimal(bareme)
      return v && b ? `${v}${ESPACE_FINE}/${ESPACE_FINE}${b}` : ''
    },
    date(iso) {
      const jour = new Date(`${iso}T00:00:00Z`)
      if (Number.isNaN(jour.getTime())) return ''
      const texte = new Intl.DateTimeFormat(langue, {
        weekday: 'long',
        day: 'numeric',
        month: 'long',
        timeZone: 'UTC',
      }).format(jour)
      return majusculeInitiale(texte)
    },
    jourMois(iso) {
      const jour = new Date(`${iso}T00:00:00Z`)
      if (Number.isNaN(jour.getTime())) return ''
      return new Intl.DateTimeFormat(langue, { day: 'numeric', month: 'long', timeZone: 'UTC' }).format(jour)
    },
    heure(instant) {
      return new Intl.DateTimeFormat(langue, { hour: '2-digit', minute: '2-digit' }).format(instant)
    },
  }
}
