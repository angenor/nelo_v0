// Le mot d'un domaine : une clé d'interface, ou un code neutre que le pack résout.
import type { Pack } from '../pack/pack'
import type { Libelle } from './types'

export function libelleDomaine(
  libelle: Libelle,
  t: (cle: string) => string,
  pack: Pick<Pack, 'libelle'>,
): string {
  return 'cle' in libelle ? t(libelle.cle) : pack.libelle(libelle.code)
}
