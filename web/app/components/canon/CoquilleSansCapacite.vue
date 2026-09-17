<script setup lang="ts">
import type { ContexteCapacites } from '~/core/contexte/types'

// Aucune capacité : ni navigation, ni page vide, ni erreur technique. L'écran nomme
// l'administrateur de l'établissement, donne son téléphone, et propose la demande (FR-026).
const props = defineProps<{ contexte: ContexteCapacites }>()
const { t } = useLibelles()
const etablissement = computed(
  () => props.contexte.etablissements.find((e) => e.id === props.contexte.etablissement_actif)!,
)
const administrateur = computed(() => etablissement.value.administrateur)
const appel = computed(() => `tel:${administrateur.value.telephone.replace(/[^\d+]/g, '')}`)
</script>

<template>
  <section class="sans-capacite" data-situation="AUCUNE_CAPACITE">
    <div class="carte">
      <h1 class="titre">{{ t('coquille.aucune_capacite.titre') }}</h1>
      <p>{{ t('coquille.aucune_capacite.texte') }}</p>
      <p class="contact" data-administrateur>
        {{
          t('coquille.aucune_capacite.contact', {
            administrateur: `${administrateur.nom} ${administrateur.prenoms}`,
            etablissement: etablissement.nom,
          })
        }}
        <span class="telephone">{{ administrateur.telephone }}</span>
      </p>
      <a :href="appel" class="action">{{ t('coquille.aucune_capacite.action') }}</a>
    </div>
  </section>
</template>

<style scoped>
.sans-capacite {
  display: flex;
  flex: 1;
  align-items: flex-start;
  justify-content: center;
  padding: 24px 16px;
}
.carte {
  min-width: 0;
  max-width: 520px;
  padding: 24px;
  border: var(--filet) solid var(--border);
  border-radius: var(--rayon-carte);
  background: var(--surface);
}
.titre {
  margin: 0 0 8px;
  font-family: var(--font-titres);
  font-weight: 700;
  font-size: 20px;
  letter-spacing: -0.02em;
}
p {
  margin: 0 0 12px;
  font-size: 14px;
  color: var(--text-muted);
}
.contact {
  color: var(--text);
}
.telephone {
  font-variant-numeric: tabular-nums;
  font-weight: 500;
  white-space: nowrap;
}
.action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: var(--cible, var(--cible-standard));
  padding: 0 16px;
  border-radius: var(--rayon-champ);
  background: var(--primary);
  color: var(--primary-ink);
  font-size: 14px;
  font-weight: 500;
}
.action:hover {
  background: var(--primary-hover);
  color: var(--primary-ink);
  text-decoration: none;
}
.action:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}
</style>
