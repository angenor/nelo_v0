<script setup lang="ts">
import type { ColonneTableau, LigneDeTableau } from './Tableau.vue'

// Une ligne ; en mode cartes, chaque cellule porte son libellé de colonne au-dessus.
defineProps<{ colonnes: ColonneTableau[]; libelles: string[]; ligne: LigneDeTableau }>()
</script>

<template>
  <tr class="ligne" :class="{ reservee: ligne.reservee }">
    <td
      v-for="(colonne, i) in colonnes"
      :key="colonne.cle"
      :class="{ fin: colonne.fin, mono: ligne.cellules[colonne.cle] && 'mono' in ligne.cellules[colonne.cle]! }"
      :data-libelle="libelles[i]"
    >
      <template v-if="ligne.cellules[colonne.cle]">
        <template v-for="cellule in [ligne.cellules[colonne.cle]!]" :key="colonne.cle">
          <span v-if="'pastille' in cellule"><CanonPastilleEtat :code="cellule.pastille" /></span>
          <span v-else-if="'canal' in cellule" class="canal">
            <CanonPastilleCanal :canal="cellule.canal" />
            <span v-if="cellule.texte">{{ cellule.texte }}</span>
          </span>
          <span v-else-if="'mono' in cellule">{{ cellule.mono }}</span>
          <span v-else class="personne">
            <span v-if="cellule.initiales" class="initiales" aria-hidden="true">{{ cellule.initiales }}</span>
            <span class="nom">{{ cellule.texte }}</span>
          </span>
        </template>
      </template>
    </td>
  </tr>
</template>

<style scoped>
@reference "../../assets/css/jetons.css";

.ligne {
  border-bottom: var(--filet) solid var(--border);
}
.ligne:last-child {
  border-bottom: 0;
}
.ligne:hover {
  background: var(--surface-sunken);
}
.ligne.reservee {
  background: var(--danger-soft);
}
td {
  padding: 10px 16px;
  vertical-align: middle;
}
td.fin {
  text-align: right;
}
td.mono {
  font-family: var(--font-mono);
  font-weight: 500;
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}
.personne {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}
.initiales {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  flex: 0 0 auto;
  border-radius: var(--rayon-pastille);
  background: var(--surface-sunken);
  color: var(--text-muted);
  font-family: var(--font-titres);
  font-weight: 600;
  font-size: 12px;
}
.reservee .initiales {
  background: var(--surface);
}
.nom {
  font-weight: 500;
}
.canal {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--text-muted);
  font-size: 13px;
}

/* En carte : la ligne est un bloc bordé, chaque cellule met son libellé au-dessus. */
[data-mode-demande='cartes'] .ligne {
  display: block;
  padding: 12px 14px;
  border: var(--filet) solid var(--border);
  border-radius: var(--rayon-carte);
  background: var(--surface);
}
[data-mode-demande='cartes'] .ligne.reservee {
  background: var(--danger-soft);
}
[data-mode-demande='cartes'] td {
  display: grid;
  gap: 2px;
  padding: 4px 0;
  text-align: left;
}
[data-mode-demande='cartes'] td::before {
  content: attr(data-libelle);
  color: var(--text-muted);
  font-family: var(--font-texte);
  font-size: 12px;
  font-weight: 500;
}
[data-mode-demande='auto'] .ligne {
  @variant max-md {
    display: block;
    padding: 12px 14px;
    border: var(--filet) solid var(--border);
    border-radius: var(--rayon-carte);
    background: var(--surface);
  }
}
[data-mode-demande='auto'] .ligne.reservee {
  @variant max-md {
    background: var(--danger-soft);
  }
}
[data-mode-demande='auto'] td {
  @variant max-md {
    display: grid;
    gap: 2px;
    padding: 4px 0;
    text-align: left;
  }
}
[data-mode-demande='auto'] td::before {
  @variant max-md {
    content: attr(data-libelle);
    color: var(--text-muted);
    font-family: var(--font-texte);
    font-size: 12px;
    font-weight: 500;
  }
}
</style>
