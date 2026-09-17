import type { Langue, Parametres } from '~/core/i18n/libelles'
import { DICTIONNAIRES, traduire } from '~/core/i18n/libelles'

function signaler(cle: string): void {
  if (import.meta.dev) console.warn(`[libellés] clé absente : ${cle}`)
}

/** La langue courante, partagée par toute l'application, et la traduction d'une clé. */
export function useLibelles() {
  const langue = useState<Langue>('langue', () => 'fr')
  return {
    langue,
    t: (cle: string, params?: Parametres) =>
      traduire(DICTIONNAIRES[langue.value], cle, params, signaler),
    changer: (nouvelle: Langue) => {
      langue.value = nouvelle
    },
  }
}
