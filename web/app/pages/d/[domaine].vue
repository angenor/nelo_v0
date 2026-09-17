<script setup lang="ts">
// L'écran d'un domaine. Pour la vie scolaire, l'appel du jour de démonstration (artboards US2
// et US3) : un champ de saisie, le ruban ancré, l'action principale en bas. Les autres domaines
// et les autres vues disent qu'ils arrivent avec leur tranche.
import { DOMAINES } from '~/core/composition/registre'
import { libelleDomaine } from '~/core/composition/libelle'
import * as demo from '~/core/demonstration/donnees'

definePageMeta({ contexteTactile: 'classe' })

const route = useRoute()
const { t } = useLibelles()
const pack = usePack()
const { composition } = useContexte()
const code = computed(() => String(route.params.domaine))
// Un domaine que la personne ne détient pas n'existe pas pour elle : retour à l'accueil.
if (!composition.value.domaines.some((d) => d.code === code.value)) {
  await navigateTo({ path: composition.value.accueil.route, query: route.query }, { replace: true })
}
const vue = computed(() => (typeof route.query.vue === 'string' ? route.query.vue : null))
const modele = computed(() => DOMAINES.find((d) => d.code === code.value))
const estAppel = computed(() => code.value === 'vie_scolaire' && vue.value === null)
const titre = computed(() => (modele.value ? libelleDomaine(modele.value.libelle, t, pack.value) : ''))

const saisie = useSaisieDemonstration()
saisie.demarrer()
const observation = ref('')

function enregistrer() {
  saisie.saisir(observation.value)
  observation.value = ''
}
function faireLAppel() {
  saisie.saisir(t('appel.fait', { heure: demo.SEANCE }))
}
</script>

<template>
  <div class="ecran-domaine">
    <div v-if="estAppel" class="contenu">
      <header class="entete-ecran">
        <p class="mot-pack" data-mot-pack="CLASSE">{{ pack.libelle('CLASSE') }}</p>
        <h1 class="titre">{{ demo.CLASSE }}</h1>
        <p class="sous-titre">
          {{
            t('appel.sous_titre', {
              jour: pack.date(demo.JOUR),
              n: demo.EFFECTIF,
              titre: pack.libelle('PROFESSEUR_PRINCIPAL'),
              nom: demo.TITULAIRE,
            })
          }}
        </p>
      </header>

      <section class="carte" aria-labelledby="appel-titre">
        <div class="ligne-titre">
          <div>
            <h2 id="appel-titre" class="titre-carte">{{ t('entree.appel_du_jour') }}</h2>
            <p class="mention">{{ t('appel.seance', { heure: demo.SEANCE }) }}</p>
          </div>
          <CanonPastilleEtat code="NON_FAIT" />
        </div>
        <p class="consigne">{{ t('appel.consigne') }}</p>
      </section>

      <section class="carte" aria-labelledby="absences-titre">
        <h2 id="absences-titre" class="titre-carte">{{ t('entree.absences') }}</h2>
        <ul class="liste">
          <li v-for="a in demo.ABSENCES" :key="a.id" class="element">
            <CanonAvatar :initiales="a.initiales" :nom="a.nom" taille="petite" />
            <span class="nom">{{ a.nom }}</span>
            <CanonPastilleEtat v-if="a.etat" :code="a.etat" />
            <span v-else class="retard">{{ t('demo.retard', { n: a.retardMinutes ?? 0 }) }}</span>
          </li>
        </ul>
      </section>

      <section class="carte" aria-labelledby="saisie-titre">
        <h2 id="saisie-titre" class="titre-carte">{{ t('appel.saisies') }}</h2>
        <form class="formulaire" @submit.prevent="enregistrer">
          <CanonChamp v-model="observation" libelle="appel.observation" aide="appel.observation_aide" />
          <CanonBouton libelle="appel.enregistrer" type="submit" />
        </form>
        <ul v-if="saisie.saisies.value.length" class="liste">
          <li v-for="s in saisie.saisies.value" :key="s.id" class="element">
            <span class="nom">{{ s.texte }}</span>
            <CanonPastilleEtat :code="s.etat" />
          </li>
        </ul>
        <p v-else class="mention">{{ t('appel.aucune_saisie') }}</p>
      </section>
    </div>

    <div v-else class="contenu">
      <h1 class="titre">{{ titre }}</h1>
      <CanonAlerte niveau="information" titre="domaine.a_venir" />
    </div>

    <div v-if="estAppel" class="pied">
      <CanonRubanSaisie :dernier-enregistrement="saisie.dernierEnregistrement.value" :en-attente="saisie.enAttente.value" />
      <div class="action">
        <CanonBouton libelle="appel.faire" variante="principal" pleine-largeur @appui="faireLAppel" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.ecran-domaine {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-height: 100%;
}
.contenu {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 16px;
  width: 100%;
  max-width: 760px;
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
.mot-pack {
  margin: 0;
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 600;
}
.sous-titre,
.mention {
  margin: 4px 0 0;
  color: var(--text-muted);
  font-size: 13px;
}
.carte {
  padding: 14px;
  border: var(--filet) solid var(--border);
  border-radius: var(--rayon-carte);
  background: var(--surface);
}
.ligne-titre {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}
.titre-carte {
  margin: 0;
  font-family: var(--font-titres);
  font-weight: 600;
  font-size: 16px;
}
.consigne {
  margin: 10px 0 0;
  font-size: 14px;
}
.liste {
  display: flex;
  flex-direction: column;
  margin: 10px 0 0;
  padding: 0;
  list-style: none;
}
.element {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border-top: var(--filet) solid var(--border);
}
.nom {
  flex: 1;
  min-width: 0;
  font-size: 14px;
  font-weight: 500;
}
.retard {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--text-muted);
}
.formulaire {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 10px;
}
.pied {
  position: sticky;
  bottom: 0;
  z-index: 2;
  background: var(--surface);
}
.action {
  padding: 8px 16px 12px;
  border-top: var(--filet) solid var(--border);
}
</style>
