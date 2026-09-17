<script lang="ts">
import { COMPOSANTS } from '~/core/composants/etats'
export const ETATS_COMPOSANT = COMPOSANTS.Avatar
</script>

<script setup lang="ts">
import type { TailleAvatar } from '~/core/composants/etats'

// Jamais une couleur seule : les initiales sont toujours rendues, sous la photo.
const props = withDefaults(
  defineProps<{ initiales: string; nom: string; photo?: string | null; taille?: TailleAvatar }>(),
  { photo: null, taille: 'grande' },
)
const photoChargee = ref(true)
const source = computed(() => (props.photo && photoChargee.value ? 'photo' : 'initiales'))
</script>

<template>
  <span class="avatar" :class="`taille-${taille}`" role="img" :aria-label="nom" :data-etat="`${taille} ${source}`">
    <span class="initiales" aria-hidden="true">{{ initiales }}</span>
    <img v-if="photo && photoChargee" :src="photo" alt="" class="photo" @error="photoChargee = false">
  </span>
</template>

<style scoped>
.avatar {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  overflow: hidden;
  border-radius: var(--rayon-pastille);
  background: var(--primary-soft);
  color: var(--primary);
  font-family: var(--font-titres);
  font-weight: 600;
}
.taille-grande {
  width: 36px;
  height: 36px;
  font-size: 14px;
}
.taille-petite {
  width: 28px;
  height: 28px;
  font-size: 12px;
  background: var(--surface-sunken);
  color: var(--text-muted);
}
.photo {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
</style>
