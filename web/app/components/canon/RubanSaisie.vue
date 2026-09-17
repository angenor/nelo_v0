<script lang="ts">
import { COMPOSANTS } from '~/core/composants/etats'
export const ETATS_COMPOSANT = COMPOSANTS.RubanSaisie
</script>

<script setup lang="ts">
import type { EtatRuban, VoixRuban } from '~/core/composants/etats'
import type { EtatReseau } from '~/core/plateforme/plateforme'

// En présentation seule : l'état est dérivé ailleurs (core/saisie/etat-ruban.ts), jamais posé
// par l'écran. Trois choses et rien d'autre ; il ne bloque jamais la saisie ; jamais rouge.
const props = defineProps<{
  etat: EtatRuban
  dernierEnregistrement: Date | null
  enAttente: number
  reseau: EtatReseau
}>()
const { t } = useLibelles()
const pack = usePack()

const VOIX: Record<EtatRuban, VoixRuban> = { enregistre: 'reussite', envoi: 'marque', hors_ligne: 'ocre' }
const FORMES: Record<EtatRuban, string> = { enregistre: 'coche', envoi: 'point', hors_ligne: 'lien_barre' }
const voix = computed(() => VOIX[props.etat])

const titre = computed(() => {
  if (props.etat === 'enregistre') return t('ruban.enregistre')
  if (props.etat === 'envoi') return t('ruban.envoi_de', { n: props.enAttente })
  return t('ruban.hors_ligne')
})
const heure = computed(() =>
  props.dernierEnregistrement ? pack.value.heure(props.dernierEnregistrement) : null,
)
const attente = computed(() => {
  if (props.etat === 'hors_ligne') {
    return props.enAttente > 0 ? t('ruban.conservees', { n: props.enAttente }) : t('ruban.aucune_attente')
  }
  if (props.etat === 'envoi') return t('ruban.continuez')
  return t('ruban.aucune_attente')
})
const lien = computed(() => {
  if (props.reseau === 'absent') return { cle: 'ruban.pas_de_lien', barres: 0 }
  if (props.reseau === 'faible') return { cle: 'ruban.lien_faible', barres: 2 }
  return { cle: 'ruban.lien_bon', barres: 3 }
})
</script>

<template>
  <div
    class="ruban"
    :class="`voix-${voix}`"
    role="status"
    aria-live="polite"
    :aria-label="t('ruban.etiquette')"
    data-porteur-etat
    :data-voix="voix"
    :data-forme="FORMES[etat]"
    :data-etat="`${etat} ${voix}`"
    :data-en-attente="enAttente"
  >
    <span class="titre">
      <InterneIcone v-if="etat === 'enregistre'" nom="coche" :taille="14" />
      <span v-else-if="etat === 'envoi'" class="point" aria-hidden="true" />
      <InterneIcone v-else nom="lien_barre" :taille="14" />
      <span class="mot">{{ titre }}</span>
    </span>
    <span class="separateur" aria-hidden="true">|</span>
    <span v-if="etat === 'hors_ligne'" class="detail fort">{{ attente }}</span>
    <span v-else class="detail">
      <template v-if="heure">{{ t('ruban.dernier_a', { heure: '' }) }}<span class="heure">{{ heure }}</span></template>
      <template v-else>{{ t('ruban.aucun_enregistrement') }}</template>
    </span>
    <span class="separateur" aria-hidden="true">|</span>
    <span class="detail">{{ etat === 'hors_ligne' ? t('ruban.rien_perdu') : attente }}</span>
    <span class="lien" :class="`qualite-${reseau}`" data-forme="barres">
      <span class="barres" aria-hidden="true">
        <span v-for="i in 3" :key="i" :class="{ allumee: i <= lien.barres }" />
      </span>
      <span>{{ t(lien.cle) }}</span>
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
.voix-ocre .titre {
  color: var(--accent);
  font-weight: 600;
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
.qualite-bon .allumee {
  background: var(--success);
}
.qualite-faible .allumee {
  background: var(--accent);
}
</style>
