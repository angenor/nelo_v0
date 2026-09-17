<script lang="ts">
import { COMPOSANTS } from '~/core/composants/etats'
import type { Canal, CodeEtat } from '~/core/composants/etats'
import type { Libelle } from '~/core/composition/types'

export const ETATS_COMPOSANT = COMPOSANTS.Tableau

export type CelluleTableau =
  | { texte: string; initiales?: string }
  | { mono: string }
  | { pastille: CodeEtat }
  | { canal: Canal; texte?: string }

export interface ColonneTableau {
  cle: string
  /** Une clé d'interface, ou un code neutre du pack (« Classe »). */
  libelle: Libelle
  /** Aligné à droite : un montant. */
  fin?: boolean
}

export interface LigneDeTableau {
  id: string
  /** La ligne d'un impayé : fond de voix rouge. */
  reservee?: boolean
  cellules: Record<string, CelluleTableau>
}
</script>

<script setup lang="ts">
import { libelleDomaine } from '~/core/composition/libelle'

// Le même balisage en lignes et en cartes : sous la rupture à deux colonnes, chaque ligne
// devient une carte, libellé au-dessus de la valeur, par CSS seul.
const props = withDefaults(
  defineProps<{
    colonnes: ColonneTableau[]
    lignes: LigneDeTableau[]
    /** Clé de la légende, lue par les lecteurs d'écran. */
    legende: string
    /** « auto » suit la largeur ; les deux autres forcent un mode (page de style). */
    mode?: 'auto' | 'lignes' | 'cartes'
  }>(),
  { mode: 'auto' },
)
const { t } = useLibelles()
const pack = usePack()
const libelles = computed(() => props.colonnes.map((c) => libelleDomaine(c.libelle, t, pack.value)))
const types = computed(() => {
  const vus = new Set<string>()
  for (const ligne of props.lignes) {
    for (const c of Object.values(ligne.cellules)) {
      vus.add('mono' in c ? 'mono' : 'pastille' in c ? 'pastille' : 'canal' in c ? 'canal' : 'texte')
    }
  }
  return [...vus]
})
const etat = computed(() => [props.mode === 'auto' ? 'lignes cartes' : props.mode, ...types.value].join(' '))
</script>

<template>
  <div class="cadre" :data-mode-demande="mode" :data-etat="etat">
    <table class="tableau">
      <caption class="lecteur">{{ t(legende) }}</caption>
      <thead>
        <tr>
          <th v-for="(colonne, i) in colonnes" :key="colonne.cle" scope="col" :class="{ fin: colonne.fin }">
            {{ libelles[i] }}
          </th>
        </tr>
      </thead>
      <tbody>
        <CanonLigneTableau v-for="ligne in lignes" :key="ligne.id" :colonnes="colonnes" :libelles="libelles" :ligne="ligne" />
      </tbody>
    </table>
  </div>
</template>

<style scoped>
@reference "../../assets/css/jetons.css";

.cadre {
  overflow: hidden;
  border: var(--filet) solid var(--border);
  border-radius: var(--rayon-carte);
  background: var(--surface);
}
.tableau {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
th {
  padding: 8px 16px;
  border-bottom: var(--filet) solid var(--border);
  background: var(--surface-sunken);
  color: var(--text-muted);
  font-size: 13px;
  font-weight: 500;
  text-align: left;
  white-space: nowrap;
}
th.fin {
  text-align: right;
}
.lecteur {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
}

/* Les cartes : forcées, ou sous la rupture à deux colonnes quand le mode suit la largeur. */
.cadre[data-mode-demande='cartes'] {
  border: 0;
  background: transparent;
}
.cadre[data-mode-demande='cartes'] thead {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip-path: inset(50%);
}
.cadre[data-mode-demande='cartes'] tbody {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.cadre[data-mode-demande='auto'] {
  @variant max-md {
    border: 0;
    background: transparent;
  }
}
.cadre[data-mode-demande='auto'] thead {
  @variant max-md {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip-path: inset(50%);
  }
}
.cadre[data-mode-demande='auto'] tbody {
  @variant max-md {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
}
</style>
