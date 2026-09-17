<script lang="ts">
import { COMPOSANTS } from '~/core/composants/etats'
export const ETATS_COMPOSANT = COMPOSANTS.RubanSaisie
</script>

<script setup lang="ts">
import type { EtatReseau } from '~/core/plateforme/plateforme'
import { deriverEtatRuban } from '~/core/saisie/etat-ruban'

// L'état est dérivé (core/saisie/etat-ruban.ts), jamais posé par l'écran ; le réseau vient de
// la plateforme. Trois choses et rien d'autre ; il ne bloque jamais la saisie ; jamais rouge.
const props = withDefaults(
  defineProps<{
    dernierEnregistrement: Date | null
    enAttente: number
    /** Page de style seulement : un réseau montré. Sinon, celui de la plateforme. */
    reseau?: EtatReseau
  }>(),
  { reseau: undefined },
)
const { t } = useLibelles()
const pack = usePack()
const reseauPlateforme = useReseau()
const vue = computed(() =>
  deriverEtatRuban(props.reseau ?? reseauPlateforme.value, props.enAttente, props.dernierEnregistrement),
)
const heure = computed(() => (vue.value.moment.heure ? pack.value.heure(vue.value.moment.heure) : ''))
</script>

<template>
  <div
    class="ruban"
    :class="`voix-${vue.voix}`"
    role="status"
    aria-live="polite"
    :aria-label="t('ruban.etiquette')"
    data-porteur-etat
    :data-voix="vue.voix"
    :data-forme="vue.forme"
    :data-etat="`${vue.etat} ${vue.voix}`"
    :data-en-attente="vue.enAttente"
  >
    <span class="titre">
      <InterneIcone v-if="vue.forme === 'coche'" nom="coche" :taille="14" />
      <span v-else-if="vue.forme === 'point'" class="point" aria-hidden="true" />
      <InterneIcone v-else nom="lien_barre" :taille="14" />
      <span>{{ t(vue.titre.cle, vue.titre.params) }}</span>
    </span>
    <span class="separateur" aria-hidden="true">|</span>
    <span class="detail" :class="{ fort: vue.etat === 'hors_ligne' }">
      {{ t(vue.moment.cle, vue.moment.params ?? { heure: '' }) }}<span v-if="heure" class="heure">{{ heure }}</span>
    </span>
    <span class="separateur" aria-hidden="true">|</span>
    <span class="detail">{{ t(vue.consigne.cle) }}</span>
    <span class="lien" :class="`barres-${vue.lien.barres}`" data-forme="barres">
      <span class="barres" aria-hidden="true">
        <span v-for="i in 3" :key="i" :class="{ allumee: i <= vue.lien.barres }" />
      </span>
      <span>{{ t(vue.lien.cle) }}</span>
    </span>
  </div>
</template>

<style scoped>
.ruban {
  position: sticky;
  bottom: 0;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 12px;
  padding: 10px 16px;
  border-top: var(--filet) solid var(--border);
  background: var(--surface);
  color: var(--text-muted);
  font-size: 13px;
}
.voix-marque {
  background: var(--surface-sunken);
}
.voix-ocre {
  border-top-color: var(--accent);
  background: var(--accent-soft);
}
.titre {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}
.voix-reussite .titre {
  color: var(--success);
}
.voix-marque .titre {
  color: var(--primary);
}
/* Hors ligne : le lien barré est ocre, le mot reste en couleur de texte (contraste AA, E-27). */
.voix-ocre .titre {
  color: var(--text);
  font-weight: 500;
}
.voix-ocre .titre :deep(.icone) {
  color: var(--accent);
}
.point {
  width: 7px;
  height: 7px;
  border-radius: var(--rayon-pastille);
  background: currentColor;
  animation: pulsation var(--pulsation-duree) var(--pulsation-courbe) infinite;
}
@keyframes pulsation {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
}
@media (prefers-reduced-motion: reduce) {
  .point {
    animation: none;
  }
}
.separateur {
  color: var(--border-strong);
}
.voix-ocre .separateur {
  color: var(--accent);
}
.fort {
  color: var(--text);
}
.heure {
  font-family: var(--font-mono);
  font-weight: 500;
  color: var(--text);
}
.lien {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}
.barres {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 12px;
}
.barres span {
  width: 3px;
  border-radius: var(--rayon-pastille);
  background: var(--border-strong);
}
.barres span:nth-child(1) {
  height: 5px;
}
.barres span:nth-child(2) {
  height: 8px;
}
.barres span:nth-child(3) {
  height: 12px;
}
.barres-3 .allumee {
  background: var(--success);
}
.barres-2 .allumee {
  background: var(--accent);
}
</style>
