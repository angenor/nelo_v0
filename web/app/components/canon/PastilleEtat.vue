<script lang="ts">
import { COMPOSANTS } from '~/core/composants/etats'
export const ETATS_COMPOSANT = COMPOSANTS.PastilleEtat
</script>

<script setup lang="ts">
import type { CodeEtat, FormePastille } from '~/core/composants/etats'
import { ETATS_METIER } from '~/core/composants/etats'

// La voix se déduit du code : un appelant ne peut pas fabriquer un rouge (FR-005).
const props = withDefaults(defineProps<{ code: CodeEtat; forme?: FormePastille }>(), { forme: 'capsule' })
const { t } = useLibelles()
const etat = computed(() => ETATS_METIER[props.code])
</script>

<template>
  <span
    class="pastille"
    :class="[`voix-${etat.voix}`, `forme-${forme}`]"
    data-porteur-etat
    :data-code="code"
    :data-voix="etat.voix"
    :data-forme="forme"
    :data-etat="`${etat.voix} ${forme}`"
  >
    <span class="point" aria-hidden="true" />
    <span>{{ t(etat.cle) }}</span>
  </span>
</template>

<style scoped>
.pastille {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: var(--pastille);
  padding: 0 10px;
  border: var(--filet) solid transparent;
  border-radius: var(--rayon-pastille);
  font-size: 13px;
  font-weight: 500;
  line-height: 1.2;
  white-space: nowrap;
}
.point {
  width: 6px;
  height: 6px;
  flex: 0 0 auto;
  border-radius: var(--rayon-pastille);
  background: currentColor;
}
.voix-reussite {
  background: var(--success-soft);
  color: var(--success);
}
.voix-ocre {
  background: var(--accent-soft);
  color: var(--accent);
}
.voix-rouge {
  background: var(--danger-soft);
  color: var(--danger);
}
.voix-neutre {
  background: var(--surface-sunken);
  color: var(--text-muted);
}
.voix-contour {
  background: transparent;
  border: var(--filet) dashed var(--accent);
  color: var(--accent);
}
.voix-contour .point {
  background: transparent;
  border: var(--filet) solid currentColor;
}
.forme-rond {
  padding: 0 2px;
  background: transparent;
}
.forme-rond.voix-contour {
  padding: 0 10px;
}
</style>
