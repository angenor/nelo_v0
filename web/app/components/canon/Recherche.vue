<script lang="ts">
import { COMPOSANTS } from '~/core/composants/etats'
export const ETATS_COMPOSANT = COMPOSANTS.Recherche
</script>

<script setup lang="ts">
import type { EtatRecherche } from '~/core/composants/etats'

// Bornée au périmètre, la portée écrite dans le champ ; le raccourci n'existe que sur poste.
// La recherche elle-même est faite par l'appelant (le serveur, demain) : ce composant affiche.
const props = withDefaults(
  defineProps<{
    /** Clé du texte de portée (« Rechercher un élève »). */
    portee: string
    /** Le périmètre, déjà résolu (« CM2 A »). */
    perimetre?: string
    modelValue?: string
    resultats?: { id: string; initiales: string; nom: string; matricule: string }[] | null
    contexte?: 'mobile' | 'poste'
    etatMontre?: EtatRecherche
  }>(),
  { perimetre: undefined, modelValue: '', resultats: null, contexte: 'mobile', etatMontre: undefined },
)
const emit = defineEmits<{ 'update:modelValue': [valeur: string]; choisir: [id: string] }>()
const { t } = useLibelles()
const plateforme = usePlateforme()
const champ = ref<HTMLInputElement | null>(null)
const id = useId()

const etat = computed<EtatRecherche>(() => {
  if (props.etatMontre) return props.etatMontre
  if (props.modelValue && props.resultats?.length === 0) return 'aucun'
  if (props.modelValue && props.resultats?.length) return 'resultats'
  if (props.modelValue) return 'saisie'
  return 'repos'
})
const texteDePortee = computed(() => (props.perimetre ? t('recherche.dans', { perimetre: props.perimetre }) : ''))

// Le libellé dépend de l'appareil : il n'existe qu'après l'hydratation, pour ne rien désaccorder.
const touches = ref('')
let retirer = () => {}
onMounted(() => {
  touches.value = plateforme.clavier.libelle('k')
  if (props.contexte === 'poste') retirer = plateforme.clavier.surRaccourci('k', () => champ.value?.focus())
})
onBeforeUnmount(() => retirer())
</script>

<template>
  <div class="recherche" :data-etat="`${etat} ${contexte}`">
    <div class="boite" :class="{ focus: etat === 'focus' }">
      <InterneIcone nom="recherche" class="loupe" />
      <input
        :id="id"
        ref="champ"
        class="saisie"
        type="search"
        :value="modelValue"
        :placeholder="t(portee)"
        :aria-label="`${t(portee)} ${texteDePortee}`.trim()"
        :aria-controls="`${id}-resultats`"
        @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      >
      <span v-if="perimetre" class="portee">{{ texteDePortee }}</span>
      <kbd v-if="contexte === 'poste' && touches" class="raccourci" :title="t('recherche.raccourci', { touches })">{{ touches }}</kbd>
    </div>
    <div :id="`${id}-resultats`" role="status" aria-live="polite">
      <ul v-if="etat === 'resultats' && resultats" class="resultats">
        <li v-for="r in resultats" :key="r.id">
          <button type="button" class="resultat" @click="emit('choisir', r.id)">
            <CanonAvatar :initiales="r.initiales" :nom="r.nom" taille="petite" />
            <span class="nom">{{ r.nom }}</span>
            <span class="matricule">{{ r.matricule }}</span>
          </button>
        </li>
      </ul>
      <p v-else-if="etat === 'aucun'" class="aucun">
        {{ t('recherche.aucun', { requete: modelValue, portee: texteDePortee }) }}
        {{ t('recherche.elargir') }}
      </p>
    </div>
  </div>
</template>

<style scoped>
.recherche {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.boite {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: var(--cible, var(--cible-standard));
  padding: 0 10px;
  border: var(--filet) solid var(--border-strong);
  border-radius: var(--rayon-champ);
  background: var(--surface);
}
.boite:focus-within,
.boite.focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-soft);
}
.loupe {
  color: var(--text-muted);
}
.saisie {
  flex: 1;
  min-width: 0;
  align-self: stretch;
  border: 0;
  background: transparent;
  color: var(--text);
  font-family: inherit;
  font-size: 16px;
  outline: none;
}
.saisie::placeholder {
  color: var(--text-muted);
}
.portee {
  flex: 0 1 auto;
  font-size: 12px;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.raccourci {
  padding: 1px 5px;
  border: var(--filet) solid var(--border);
  border-radius: var(--rayon-micro);
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-muted);
  white-space: nowrap;
}
.resultats {
  margin: 0;
  padding: 4px;
  list-style: none;
  border: var(--filet) solid var(--border);
  border-radius: var(--rayon-carte);
  background: var(--surface);
}
.resultat {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  min-height: var(--cible, var(--cible-standard));
  padding: 0 8px;
  border: 0;
  border-radius: var(--rayon-champ);
  background: transparent;
  color: var(--text);
  font-family: inherit;
  font-size: 14px;
  text-align: left;
  cursor: pointer;
}
.resultat:hover,
.resultat:focus-visible {
  background: var(--surface-sunken);
  outline: none;
}
.nom {
  font-weight: 500;
}
.matricule {
  margin-left: auto;
  font-family: var(--font-mono);
  font-weight: 500;
  font-size: 13px;
  color: var(--text-muted);
}
.aucun {
  margin: 0;
  font-size: 13px;
  color: var(--text-muted);
}
</style>
