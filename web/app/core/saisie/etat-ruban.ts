// L'état du ruban, dérivé et jamais posé (data-model.md § 3, research.md R-04). Trois entrées,
// trois choses dites : le titre, le moment (heure du dernier enregistrement, ou compte conservé
// hors ligne), la consigne ; plus la qualité du lien. Aucune voix rouge n'est possible.
import type { EtatRuban, VoixRuban } from '../composants/etats'
import type { EtatReseau } from '../plateforme/plateforme'

export type FormeRuban = 'coche' | 'point' | 'lien_barre'

export interface Mot {
  cle: string
  params?: { n: number }
}

export interface VueRuban {
  etat: EtatRuban
  voix: VoixRuban
  forme: FormeRuban
  enAttente: number
  titre: Mot
  moment: Mot & { heure: Date | null }
  consigne: Mot
  lien: Mot & { barres: 0 | 2 | 3 }
}

const LIENS: Record<EtatReseau, VueRuban['lien']> = {
  bon: { cle: 'ruban.lien_bon', barres: 3 },
  faible: { cle: 'ruban.lien_faible', barres: 2 },
  absent: { cle: 'ruban.pas_de_lien', barres: 0 },
}

export function deriverEtatRuban(
  reseau: EtatReseau,
  enAttenteBrut: number,
  dernierEnregistrement: Date | null,
): VueRuban {
  const enAttente = Number.isInteger(enAttenteBrut) && enAttenteBrut > 0 ? enAttenteBrut : 0
  const lien = LIENS[reseau]
  const heure = dernierEnregistrement
  const moment: VueRuban['moment'] = heure
    ? { cle: 'ruban.dernier_a', heure }
    : { cle: 'ruban.aucun_enregistrement', heure: null }

  if (reseau === 'absent') {
    return {
      etat: 'hors_ligne',
      voix: 'ocre',
      forme: 'lien_barre',
      enAttente,
      titre: { cle: 'ruban.hors_ligne' },
      moment:
        enAttente > 0
          ? { cle: 'ruban.conservees', params: { n: enAttente }, heure: null }
          : { cle: 'ruban.aucune_attente', heure: null },
      consigne: { cle: 'ruban.rien_perdu' },
      lien,
    }
  }
  if (enAttente > 0) {
    return {
      etat: 'envoi',
      voix: 'marque',
      forme: 'point',
      enAttente,
      titre: { cle: 'ruban.envoi_de', params: { n: enAttente } },
      moment,
      consigne: { cle: 'ruban.continuez' },
      lien,
    }
  }
  return {
    etat: 'enregistre',
    voix: 'reussite',
    forme: 'coche',
    enAttente,
    titre: { cle: 'ruban.enregistre' },
    moment,
    consigne: { cle: 'ruban.aucune_attente' },
    lien,
  }
}
