<script lang="ts">
import { COMPOSANTS } from '~/core/composants/etats'
export const ETATS_COMPOSANT = COMPOSANTS.PastilleCanal
</script>

<script setup lang="ts">
import type { Canal } from '~/core/composants/etats'

// Le SMS est un canal de premier rang : il est mis en avant, et son coût s'écrit à côté
// de l'action qui l'engage (constitution XIII). Le coût est un entier d'unité mineure.
const props = withDefaults(defineProps<{ canal: Canal; cout?: number | null }>(), { cout: null })
const { t } = useLibelles()
const pack = usePack()
const cout = computed(() => (props.cout === null ? '' : pack.value.montant(props.cout)))
</script>

<template>
  <span class="canal" :data-canal="canal" :data-etat="`${canal} ${cout ? 'avec_cout' : 'sans_cout'}`">
    <span class="pastille" :class="{ avant: canal === 'SMS' }" data-porteur-etat data-forme="capsule">
      {{ t(`canal.${canal}`) }}
    </span>
    <span v-if="cout" class="cout">{{ t('canal.cout', { montant: cout }) }}</span>
  </span>
</template>

<style scoped>
.canal {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}
.pastille {
  display: inline-flex;
  align-items: center;
  min-height: 22px;
  padding: 0 8px;
  border: var(--filet) solid var(--border-strong);
  border-radius: var(--rayon-pastille);
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-weight: 500;
  font-size: 12px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.pastille.avant {
  border-color: var(--primary);
  background: var(--primary-soft);
  color: var(--primary);
}
.cout {
  font-family: var(--font-mono);
  font-weight: 500;
  font-size: 12px;
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
}
</style>
