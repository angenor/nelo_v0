<script setup lang="ts">
// L'accueil : il est le domaine pour une personne mono-domaine (FR-023), un tableau composé
// d'un bloc par domaine sinon (FR-024) ; sans capacité, la coquille rend l'écran qui nomme
// l'administrateur.
import { libelleDomaine } from '~/core/composition/libelle'
import * as demo from '~/core/demonstration/donnees'

definePageMeta({ contexteTactile: 'standard' })

const route = useRoute()
const { t } = useLibelles()
const pack = usePack()
const { composition } = useContexte()

if (composition.value.situation === 'MONO_DOMAINE') {
  await navigateTo({ path: composition.value.accueil.route, query: route.query }, { replace: true })
}

const blocs = computed(() =>
  composition.value.domaines.map((domaine) => {
    const bloc = demo.BLOCS[domaine.code]
    let valeur = ''
    if (bloc?.montant !== undefined) valeur = pack.value.montant(bloc.montant)
    else if (bloc?.nombre !== undefined) valeur = String(bloc.nombre)
    else if (bloc?.valeurCle) valeur = t(bloc.valeurCle)
    return {
      domaine,
      nom: libelleDomaine(domaine.libelle, t, pack.value),
      valeur,
      detail: bloc ? t(bloc.cle, bloc.parametres) : undefined,
      reservee: bloc?.reservee ?? false,
    }
  }),
)
</script>

<template>
  <section v-if="composition.situation !== 'AUCUNE_CAPACITE'" class="tableau-compose">
    <header>
      <h1 class="titre">{{ t('coquille.tableau_compose') }}</h1>
      <p class="sous-titre">{{ t('coquille.tableau_sous_titre', { jour: pack.date(demo.JOUR) }) }}</p>
    </header>
    <div class="blocs">
      <CanonCarteIndicateur
        v-for="bloc in blocs"
        :key="bloc.domaine.code"
        :data-bloc-domaine="bloc.domaine.code"
        :libelle="bloc.domaine.libelle"
        :valeur="bloc.valeur"
        :detail="bloc.detail"
        :reservee="bloc.reservee"
        :vers="bloc.domaine.route"
      />
    </div>
  </section>
</template>

<style scoped>
.tableau-compose {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
  max-width: 960px;
  margin: 0 auto;
  padding: 20px 16px;
}
.titre {
  margin: 0;
  font-family: var(--font-titres);
  font-weight: 700;
  font-size: 20px;
  letter-spacing: -0.02em;
}
.sous-titre {
  margin: 4px 0 0;
  color: var(--text-muted);
  font-size: 13px;
}
.blocs {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 200px), 1fr));
  gap: 12px;
}
</style>
