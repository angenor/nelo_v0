<script lang="ts">
import { COMPOSANTS } from '~/core/composants/etats'
export const ETATS_COMPOSANT = COMPOSANTS.CarteIndicateur
</script>

<script setup lang="ts">
import type { SensVariation } from '~/core/composants/etats'
import type { Parametres } from '~/core/i18n/libelles'

// Un chiffre clé déjà calculé et mis en forme par l'appelant : la carte ne calcule rien.
// Chaque sens a sa flèche et son mot ; la valeur réservée (rouge) ne sert qu'à un impayé.
const props = withDefaults(
  defineProps<{
    /** Clé du libellé. */
    libelle: string
    parametres?: Parametres
    valeur: string
    variation?: { sens: SensVariation; texte: string } | null
    reservee?: boolean
    /** Rend toute la carte cliquable vers une route. */
    vers?: string
  }>(),
  { parametres: undefined, variation: null, reservee: false, vers: undefined },
)
const { t } = useLibelles()
const FLECHES = { positive: 'fleche_haut', negative: 'fleche_bas', neutre: 'egal' } as const
const MOTS = { positive: 'indicateur.hausse', negative: 'indicateur.baisse', neutre: 'indicateur.stable' } as const
const etat = computed(() => [props.variation?.sens ?? 'neutre', props.reservee ? 'reservee' : 'ordinaire'].join(' '))
</script>

<template>
  <component :is="vers ? resolveComponent('NuxtLink') : 'div'" :to="vers" class="carte" :class="{ lien: vers }" :data-etat="etat">
    <div class="libelle">{{ t(libelle, parametres) }}</div>
    <div class="valeur" :class="{ reservee }" :data-voix="reservee ? 'rouge' : undefined">{{ valeur }}</div>
    <div v-if="variation" class="variation" :class="`sens-${variation.sens}`" data-porteur-etat data-forme="fleche">
      <InterneIcone :nom="FLECHES[variation.sens]" :taille="14" />
      <span class="lecteur">{{ t(MOTS[variation.sens]) }}</span>
      <span>{{ variation.texte }}</span>
    </div>
  </component>
</template>

<style scoped>
.carte {
  display: block;
  padding: 16px;
  border: var(--filet) solid var(--border);
  border-radius: var(--rayon-carte);
  background: var(--surface);
  color: var(--text);
  min-width: 0;
}
.carte.lien {
  min-height: var(--cible, var(--cible-standard));
  text-decoration: none;
}
.carte.lien:hover {
  border-color: var(--border-strong);
  text-decoration: none;
}
.carte.lien:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}
.libelle {
  font-size: 13px;
  color: var(--text-muted);
}
.valeur {
  margin: 6px 0 4px;
  font-family: var(--font-titres);
  font-weight: 600;
  font-size: 26px;
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
  overflow-wrap: anywhere;
}
.valeur.reservee {
  color: var(--danger);
}
.variation {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-muted);
}
.sens-positive {
  color: var(--success);
}
.lecteur {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
}
</style>
