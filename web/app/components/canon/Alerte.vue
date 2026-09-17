<script lang="ts">
import { COMPOSANTS } from '~/core/composants/etats'
export const ETATS_COMPOSANT = COMPOSANTS.Alerte
</script>

<script setup lang="ts">
import type { NiveauAlerte } from '~/core/composants/etats'
import type { Parametres } from '~/core/i18n/libelles'

// Un bloc, un seul niveau, une icône par niveau. Le danger est réservé à l'impayé et à
// l'absence non justifiée : c'est à l'appelant de le mériter (voir composants.md § 11).
const props = withDefaults(
  defineProps<{
    niveau: NiveauAlerte
    /** Clé du titre. */
    titre: string
    /** Clé du corps. */
    corps?: string
    parametres?: Parametres
    /** Une action facultative : sa clé et sa route. */
    action?: { libelle: string; vers: string } | null
  }>(),
  { corps: undefined, parametres: undefined, action: null },
)
const { t } = useLibelles()
const ICONES = { information: 'information', attente: 'exclamation', danger: 'triangle', enregistre: 'coche' } as const
const VOIX = { information: 'neutre', attente: 'ocre', danger: 'rouge', enregistre: 'reussite' } as const
const etat = computed(() => `${props.niveau} ${props.action ? 'avec_action' : 'sans_action'}`)
</script>

<template>
  <div
    class="alerte"
    :class="`niveau-${niveau}`"
    :role="niveau === 'danger' ? 'alert' : 'status'"
    data-porteur-etat
    :data-niveau="niveau"
    :data-voix="VOIX[niveau]"
    data-forme="icone"
    :data-etat="etat"
  >
    <InterneIcone :nom="ICONES[niveau]" :taille="18" class="symbole" />
    <div class="texte">
      <p class="titre">
        <span class="lecteur">{{ t(`alerte.niveau.${niveau}`) }} : </span>{{ t(titre, parametres) }}
      </p>
      <p v-if="corps || $slots.default" class="corps">
        <slot>{{ corps ? t(corps, parametres) : '' }}</slot>
      </p>
      <NuxtLink v-if="action" :to="action.vers" class="action">{{ t(action.libelle) }}</NuxtLink>
    </div>
  </div>
</template>

<style scoped>
.alerte {
  display: flex;
  gap: 12px;
  padding: 12px 14px;
  border: var(--filet) solid var(--border);
  border-radius: var(--rayon-carte);
  background: var(--surface);
  color: var(--text);
}
.symbole {
  margin-top: 1px;
  color: var(--text-muted);
}
.niveau-attente {
  border-color: var(--accent);
  background: var(--accent-soft);
}
.niveau-attente .symbole {
  color: var(--accent);
}
.niveau-danger {
  border-color: var(--danger);
  background: var(--danger-soft);
}
.niveau-danger .symbole {
  color: var(--danger);
}
.niveau-enregistre {
  background: var(--success-soft);
}
.niveau-enregistre .symbole {
  color: var(--success);
}
.texte {
  min-width: 0;
}
.titre {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
}
.corps {
  margin: 2px 0 0;
  font-size: 13px;
  color: var(--text-muted);
}
.action {
  display: inline-flex;
  align-items: center;
  min-width: var(--cible-plancher);
  min-height: var(--cible, var(--cible-standard));
  font-size: 13px;
  font-weight: 500;
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
