<script lang="ts">
import { COMPOSANTS } from '~/core/composants/etats'
export const ETATS_COMPOSANT = COMPOSANTS.Coquille
</script>

<script setup lang="ts">
import type { ContexteTactile } from '~/core/composants/etats'
import type { Composition } from '~/core/composition/types'
import type { ContexteCapacites } from '~/core/contexte/types'

// En présentation seule : la composition est décidée par composer(contexte), jamais ici, et
// jamais depuis un rôle. L'écran vient par le slot.
const props = withDefaults(
  defineProps<{
    composition: Composition
    contexte: ContexteCapacites
    routeActive: string
    contexteTactile?: ContexteTactile
    montrerRetour?: boolean
    /** Sans capacité, l'écran qui nomme l'administrateur remplace l'accueil ; « à propos » reste atteignable. */
    surAccueil?: boolean
    /** Page de style : une coquille réduite, sans repère principal. */
    apercu?: boolean
    /** L'année choisie sur cet appareil (research.md R-21) ; sinon l'année active du contexte. */
    anneeChoisie?: string | null
  }>(),
  {
    contexteTactile: 'standard',
    montrerRetour: false,
    surAccueil: true,
    apercu: false,
    anneeChoisie: null,
  },
)
// La coquille relaie les gestes de l'en-tête : elle ne choisit rien, elle ne stocke rien.
const emit = defineEmits<{
  retour: []
  changerEtablissement: [identifiant: string]
  changerAnnee: [identifiant: string]
  deconnexion: []
}>()
const tiroirOuvert = ref(false)
const sansCapacite = computed(() => props.composition.situation === 'AUCUNE_CAPACITE')
const enFamilles = computed(() => props.composition.situation === 'MULTI_FAMILLES')
const styleTactile = fournirContexteTactile(toRef(props, 'contexteTactile'))
watch(
  () => props.routeActive,
  () => {
    tiroirOuvert.value = false
  },
)
</script>

<template>
  <div
    class="coquille"
    :class="{ apercu, 'avec-barre-basse': !sansCapacite && !enFamilles }"
    :style="styleTactile"
    :data-situation="composition.situation"
    :data-etat="composition.situation"
    :data-contexte-tactile="contexteTactile"
  >
    <CanonCoquilleEntete
      :contexte="contexte"
      :accueil="composition.accueil.route"
      :montrer-menu="enFamilles"
      :montrer-retour="montrerRetour"
      :menu-ouvert="tiroirOuvert"
      :annee-choisie="anneeChoisie"
      @menu="tiroirOuvert = !tiroirOuvert"
      @retour="emit('retour')"
      @changer-etablissement="emit('changerEtablissement', $event)"
      @changer-annee="emit('changerAnnee', $event)"
      @deconnexion="emit('deconnexion')"
    />
    <div class="corps">
      <CanonCoquilleNavigation
        v-if="!sansCapacite"
        class="laterale"
        :composition="composition"
        :route-active="routeActive"
        disposition="laterale"
      />
      <component :is="apercu ? 'div' : 'main'" :id="apercu ? undefined : 'principal'" class="ecran">
        <CanonCoquilleSansCapacite v-if="sansCapacite && surAccueil" :contexte="contexte" />
        <slot />
      </component>
    </div>
    <CanonCoquilleNavigation
      v-if="!sansCapacite && !enFamilles"
      class="basse"
      :composition="composition"
      :route-active="routeActive"
      disposition="basse"
    />
    <div v-if="enFamilles && tiroirOuvert" class="tiroir">
      <div class="voile" aria-hidden="true" @click="tiroirOuvert = false" />
      <CanonCoquilleNavigation
        class="panneau"
        :composition="composition"
        :route-active="routeActive"
        disposition="tiroir"
      />
    </div>
  </div>
</template>

<style scoped>
@reference "../../assets/css/jetons.css";

.coquille {
  position: relative;
  display: flex;
  flex-direction: column;
  width: 100%;
  min-width: 0;
  height: 100dvh;
  background: var(--bg);
  color: var(--text);
}
.coquille.apercu {
  height: 520px;
  overflow: hidden;
  border: var(--filet) solid var(--border-strong);
  border-radius: var(--rayon-carte);
}
.corps {
  display: flex;
  flex: 1;
  min-height: 0;
}
.ecran {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
  overflow: auto;
  background: var(--bg);
}
.laterale {
  width: 208px;
  flex: 0 0 auto;
  overflow: auto;
  border-right: var(--filet) solid var(--border);
  background: var(--surface);
  @variant max-md {
    display: none;
  }
}
.basse {
  flex: 0 0 auto;
  border-top: var(--filet) solid var(--border);
  background: var(--surface);
  @variant md {
    display: none;
  }
}
.tiroir {
  position: absolute;
  inset: 0;
  z-index: 10;
  display: flex;
  @variant md {
    display: none;
  }
}
.voile {
  position: absolute;
  inset: 0;
  background: var(--text);
  opacity: 0.4;
}
.panneau {
  position: relative;
  width: min(280px, 85%);
  overflow: auto;
  background: var(--surface);
  box-shadow: 0 0 24px var(--border-strong);
}
</style>
