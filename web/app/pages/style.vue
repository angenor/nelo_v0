<script setup lang="ts">
// La page de style : les quatorze composants, chaque état en clair et en sombre, sur des
// données de démonstration du primaire. Elle itère les énumérations que chaque composant
// exporte. Page de développement : un crochet de nuxt.config.ts la retire de la construction.
import { ETATS_COMPOSANT as AVATAR } from '~/components/canon/Avatar.vue'
import { ETATS_COMPOSANT as BOUTON } from '~/components/canon/Bouton.vue'
import { ETATS_COMPOSANT as COQUILLE } from '~/components/canon/Coquille.vue'
import { ETATS_COMPOSANT as CANAL } from '~/components/canon/PastilleCanal.vue'
import { ETATS_COMPOSANT as PASTILLE } from '~/components/canon/PastilleEtat.vue'
import { ETATS_COMPOSANT as RECHERCHE } from '~/components/canon/Recherche.vue'
import type { ColonneTableau, LigneDeTableau } from '~/components/canon/Tableau.vue'
import type { CodeEtat } from '~/core/composants/etats'
import { CONTEXTES_TACTILES, ETATS_METIER } from '~/core/composants/etats'
import { composer } from '~/core/composition/composer'
import * as demo from '~/core/demonstration/donnees'
import { PERSONA_PAR_SITUATION, PERSONAS } from '~/core/demonstration/personas'

definePageMeta({ contexteTactile: 'standard', sansCoquille: true })

const { t } = useLibelles()
const pack = usePack()

const LIBELLES_BOUTON = {
  principal: 'demo.enregistrer_appel',
  secondaire: 'demo.imprimer_liste',
  discret: 'demo.annuler',
  danger: 'demo.supprimer_inscription',
} as const
const ETATS_BOUTON_INTERACTIFS = BOUTON.ETATS.filter((e) => e !== 'inactif')

const nom = ref('Koffi Aya Estelle')
const effectif = ref('36')
const matricule = ref('ELV-2026-0413')
const motif = ref('')
const note = computed(() => pack.value.decimal(demo.NOTE_DICTEE.valeur))
const affectation = ref('cm2a')
const montant = computed(() => pack.value.montant(demo.MONTANT_VERSE, { symbole: false }))
const caseSms = ref(true)
const casePapier = ref(false)
const interrupteurs = reactive({ resultats: true, paiement: false, assistance: false })

const CODES = Object.keys(ETATS_METIER) as CodeEtat[]
const parVoix = (voix: string) => CODES.filter((c) => ETATS_METIER[c].voix === voix)

const requetes = { repos: '', focus: '', saisie: 'Koff', resultats: 'Koff', aucun: 'Xyz' } as const
const resultatsPour = (etat: keyof typeof requetes) =>
  etat === 'resultats' ? demo.RESULTATS_RECHERCHE : etat === 'aucun' ? [] : null

const ongletActif = ref('absences')
const onglets = [
  { cle: 'scolarite', libelle: 'demo.onglet_scolarite' },
  { cle: 'absences', libelle: 'demo.onglet_absences', compte: 3 },
  { cle: 'notes', libelle: 'demo.onglet_notes' },
  { cle: 'paiements', libelle: 'demo.onglet_paiements' },
]

const colonnes: ColonneTableau[] = [
  { cle: 'eleve', libelle: { cle: 'demo.col_eleve' } },
  { cle: 'matricule', libelle: { cle: 'demo.col_matricule' } },
  { cle: 'classe', libelle: { code: 'CLASSE' } },
  { cle: 'reste', libelle: { cle: 'demo.col_reste' }, fin: true },
  { cle: 'etat', libelle: { cle: 'demo.col_etat' } },
  { cle: 'contact', libelle: { cle: 'demo.col_contact' } },
]
const lignes = computed<LigneDeTableau[]>(() =>
  demo.ELEVES.map((e) => ({
    id: e.id,
    reservee: e.etat === 'IMPAYE',
    cellules: {
      eleve: { texte: e.nom, initiales: e.initiales },
      matricule: { mono: e.matricule },
      classe: { mono: e.classe },
      reste: { mono: pack.value.montant(e.resteAPayer) },
      etat: { pastille: e.etat },
      contact: { canal: e.canal, texte: pack.value.jourMois(e.dernierContact) },
    },
  })),
)

const dernier = new Date(demo.DERNIER_ENREGISTREMENT)
const plusTard = new Date(dernier.getTime() + 2 * 60_000)
const rubans = [
  { etat: 'enregistre', reseau: 'bon', dernier, attente: 0 },
  { etat: 'envoi', reseau: 'faible', dernier: plusTard, attente: 2 },
  { etat: 'hors_ligne', reseau: 'absent', dernier: plusTard, attente: 4 },
] as const
const rubansDeBord = [
  { cle: 'style.aucun_enregistrement', etat: 'enregistre', reseau: 'bon', dernier: null, attente: 0 },
  { cle: 'style.hors_ligne_sans_attente', etat: 'hors_ligne', reseau: 'absent', dernier: null, attente: 0 },
] as const

const coquilles = COQUILLE.SITUATIONS.map((situation) => {
  const contexte = PERSONAS[PERSONA_PAR_SITUATION[situation]]
  return { situation, contexte, composition: composer(contexte) }
})
const photo = '/icones/180.png'
</script>

<template>
  <div class="page">
    <header class="entete">
      <h1 class="titre">{{ t('style.titre') }}</h1>
      <p class="intro">{{ t('style.intro') }}</p>
    </header>

    <InterneSectionStyle composant="Bouton" :numero="1">
      <div class="grille">
        <template v-for="variante in BOUTON.VARIANTES" :key="variante">
          <InterneEtatStyle v-for="etat in ETATS_BOUTON_INTERACTIFS" :key="etat" :etats="`${variante} ${etat}`">
            <CanonBouton :libelle="LIBELLES_BOUTON[variante]" :variante="variante" :etat-montre="etat" />
          </InterneEtatStyle>
        </template>
      </div>
      <InterneEtatStyle etats="principal inactif" class="espace">
        <CanonBouton libelle="demo.enregistrer_appel" variante="principal" :inactif="{ raison: 'demo.raison_selection' }" />
      </InterneEtatStyle>
      <p class="sous-titre">{{ t('style.contextes') }}</p>
      <div class="rangee">
        <div v-for="contexte in CONTEXTES_TACTILES" :key="contexte" :style="{ '--cible': CIBLES[contexte] }" :data-contexte-tactile="contexte">
          <CanonBouton :libelle="`style.contexte.${contexte}`" variante="secondaire" />
        </div>
      </div>
    </InterneSectionStyle>

    <InterneSectionStyle composant="Champ" :numero="2">
      <div class="grille large">
        <InterneEtatStyle etats="texte repos">
          <CanonChamp v-model="nom" libelle="demo.nom_eleve" />
        </InterneEtatStyle>
        <InterneEtatStyle etats="texte focus">
          <CanonChamp v-model="nom" libelle="demo.nom_eleve" etat-montre="focus" />
        </InterneEtatStyle>
        <InterneEtatStyle etats="nombre erreur">
          <CanonChamp v-model="effectif" libelle="demo.effectif_present" type="nombre" erreur="demo.erreur_effectif" :parametres-erreur="{ n: demo.EFFECTIF }" />
        </InterneEtatStyle>
        <InterneEtatStyle etats="texte inactif">
          <CanonChamp v-model="matricule" libelle="demo.matricule" mono inactif />
        </InterneEtatStyle>
        <InterneEtatStyle etats="texte aide">
          <CanonChamp v-model="motif" libelle="demo.motif" aide="demo.motif_aide" />
        </InterneEtatStyle>
        <InterneEtatStyle etats="nombre unite">
          <CanonChamp :model-value="note" libelle="demo.note_dictee" type="nombre" :unite="`/ ${demo.NOTE_DICTEE.bareme}`" />
        </InterneEtatStyle>
        <InterneEtatStyle etats="choix">
          <CanonChamp
            v-model="affectation"
            libelle="demo.affectation"
            type="choix"
            :options="[{ valeur: 'cm2a', libelle: `${pack.libelle('CLASSE')} ${demo.CLASSE}` }]"
          />
        </InterneEtatStyle>
        <InterneEtatStyle etats="nombre unite">
          <CanonChamp :model-value="montant" libelle="demo.montant_verse" type="nombre" :unite="pack.devise.symbole" />
        </InterneEtatStyle>
        <InterneEtatStyle etats="case">
          <CanonChamp v-model="caseSms" libelle="demo.recu_sms" type="case" />
          <CanonChamp v-model="casePapier" libelle="demo.recu_papier" type="case" />
        </InterneEtatStyle>
      </div>
    </InterneSectionStyle>

    <InterneSectionStyle composant="Interrupteur" :numero="3">
      <div class="pile">
        <CanonInterrupteur v-model="interrupteurs.resultats" libelle="demo.resultats_en_ligne" />
        <CanonInterrupteur v-model="interrupteurs.paiement" libelle="demo.paiement_trois_fois" />
        <CanonInterrupteur v-model="interrupteurs.assistance" libelle="demo.assistance" :inactif="{ raison: 'demo.assistance_raison' }" />
      </div>
    </InterneSectionStyle>

    <InterneSectionStyle composant="PastilleEtat" :numero="4">
      <div v-for="forme in PASTILLE.FORMES" :key="forme" class="pile espace">
        <InterneEtatStyle v-for="voix in PASTILLE.VOIX" :key="voix" :etats="`${voix} ${forme}`">
          <div class="rangee">
            <CanonPastilleEtat v-for="code in parVoix(voix)" :key="code" :code="code" :forme="forme" />
          </div>
        </InterneEtatStyle>
      </div>
    </InterneSectionStyle>

    <InterneSectionStyle composant="PastilleCanal" :numero="5">
      <InterneEtatStyle etats="sans_cout">
        <div class="rangee">
          <CanonPastilleCanal v-for="canal in CANAL.CANAUX" :key="canal" :canal="canal" />
        </div>
      </InterneEtatStyle>
      <InterneEtatStyle etats="SMS avec_cout" class="espace">
        <div class="rangee">
          <CanonBouton libelle="demo.envoyer_sms" variante="principal" />
          <CanonPastilleCanal canal="SMS" :cout="demo.COUT_SMS" />
          <span class="mention">{{ t('demo.cout_classe', { montant: pack.montant(demo.COUT_SMS * demo.EFFECTIF), n: demo.EFFECTIF }) }}</span>
        </div>
      </InterneEtatStyle>
    </InterneSectionStyle>

    <InterneSectionStyle composant="Recherche" :numero="6">
      <div class="pile">
        <InterneEtatStyle v-for="etat in RECHERCHE.ETATS" :key="etat" :etats="etat">
          <CanonRecherche
            :model-value="requetes[etat]"
            portee="demo.rechercher_eleve"
            :perimetre="demo.CLASSE"
            :resultats="resultatsPour(etat)"
            :contexte="etat === 'repos' ? 'poste' : 'mobile'"
            :etat-montre="etat === 'focus' ? 'focus' : undefined"
          />
        </InterneEtatStyle>
      </div>
    </InterneSectionStyle>

    <InterneSectionStyle composant="Avatar" :numero="7">
      <div class="rangee">
        <template v-for="source in AVATAR.SOURCES" :key="source">
          <InterneEtatStyle v-for="taille in AVATAR.TAILLES" :key="taille" :etats="`${taille} ${source}`">
            <CanonAvatar initiales="AK" :nom="demo.TITULAIRE" :taille="taille" :photo="source === 'photo' ? photo : null" />
          </InterneEtatStyle>
        </template>
        <div class="identite">
          <span class="nom-personne">{{ demo.TITULAIRE }}</span>
          <span class="mention">{{ pack.libelle('PROFESSEUR_PRINCIPAL') }} · {{ demo.CLASSE }}</span>
        </div>
      </div>
    </InterneSectionStyle>

    <InterneSectionStyle composant="FilAriane" :numero="8">
      <CanonFilAriane
        :segments="[
          { libelle: t('cycle.PRIMAIRE'), route: '/style' },
          { libelle: 'CM2', route: '/style' },
          { libelle: demo.CLASSE, route: '/style' },
          { libelle: demo.ELEVES[0]!.nom },
        ]"
      />
    </InterneSectionStyle>

    <InterneSectionStyle composant="Onglets" :numero="9">
      <CanonOnglets v-model="ongletActif" :onglets="onglets" />
    </InterneSectionStyle>

    <InterneSectionStyle composant="CarteIndicateur" :numero="10">
      <div class="grille cartes">
        <CanonCarteIndicateur
          libelle="demo.presents"
          :valeur="`${demo.INDICATEURS.presents.presents} / ${demo.INDICATEURS.presents.effectif}`"
          :variation="{ sens: 'positive', texte: t('demo.variation_hier', { n: demo.INDICATEURS.presents.variation }) }"
        />
        <CanonCarteIndicateur
          libelle="demo.notes_saisies"
          :valeur="String(demo.INDICATEURS.notesSaisies.valeur)"
          :variation="{ sens: 'negative', texte: t('demo.variation_dictee', { n: -demo.INDICATEURS.notesSaisies.variation }) }"
        />
        <CanonCarteIndicateur
          libelle="demo.inscrits"
          :valeur="String(demo.INDICATEURS.inscrits.valeur)"
          :variation="{ sens: 'neutre', texte: t('demo.stable') }"
        />
        <CanonCarteIndicateur
          libelle="demo.reste_classe"
          :parametres="{ classe: demo.CLASSE }"
          :valeur="pack.montant(demo.INDICATEURS.resteAPayer.montant)"
          :variation="{ sens: 'neutre', texte: t('demo.impaye_reserve') }"
          reservee
        />
      </div>
    </InterneSectionStyle>

    <InterneSectionStyle composant="Alerte" :numero="11">
      <div class="pile">
        <CanonAlerte niveau="information" titre="demo.alerte_info_titre" corps="demo.alerte_info_corps" :parametres="{ heure: demo.SEANCE }" />
        <CanonAlerte
          niveau="attente"
          titre="demo.alerte_attente_titre"
          corps="demo.alerte_attente_corps"
          :parametres="{ n: 3 }"
          :action="{ libelle: 'demo.recharger', vers: '/style' }"
        />
        <CanonAlerte
          niveau="danger"
          titre="demo.alerte_danger_titre"
          corps="demo.alerte_danger_corps"
          :parametres="{ nom: 'Yao Serge Emmanuel' }"
          :action="{ libelle: 'demo.justifier', vers: '/style' }"
        />
        <CanonAlerte
          niveau="enregistre"
          titre="demo.alerte_enregistre_titre"
          corps="demo.alerte_enregistre_corps"
          :parametres="{ numero: demo.RECU.numero }"
        />
      </div>
    </InterneSectionStyle>

    <InterneSectionStyle composant="Tableau" :numero="12">
      <div class="pile">
        <InterneEtatStyle etats="lignes">
          <p class="mention">{{ t('demo.mode_lignes') }}</p>
          <div class="defilement">
            <CanonTableau :colonnes="colonnes" :lignes="lignes" legende="demo.legende_tableau" mode="lignes" />
          </div>
        </InterneEtatStyle>
        <InterneEtatStyle etats="lignes cartes">
          <p class="mention">{{ t('demo.mode_auto') }}</p>
          <div class="defilement">
            <CanonTableau :colonnes="colonnes" :lignes="lignes.slice(0, 2)" legende="demo.legende_tableau" />
          </div>
        </InterneEtatStyle>
        <InterneEtatStyle etats="cartes">
          <p class="mention">{{ t('demo.mode_cartes') }}</p>
          <div class="etroit">
            <CanonTableau :colonnes="colonnes" :lignes="lignes.slice(1, 3)" legende="demo.legende_tableau" mode="cartes" />
          </div>
        </InterneEtatStyle>
      </div>
    </InterneSectionStyle>

    <InterneSectionStyle composant="RubanSaisie" :numero="13">
      <div class="pile">
        <InterneEtatStyle v-for="r in rubans" :key="r.etat" :etats="r.etat">
          <div class="cadre-ruban">
            <CanonRubanSaisie :reseau="r.reseau" :dernier-enregistrement="r.dernier" :en-attente="r.attente" />
          </div>
        </InterneEtatStyle>
        <InterneEtatStyle v-for="r in rubansDeBord" :key="r.cle" :etats="r.etat">
          <p class="mention">{{ t(r.cle) }}</p>
          <div class="cadre-ruban">
            <CanonRubanSaisie :reseau="r.reseau" :dernier-enregistrement="r.dernier" :en-attente="r.attente" />
          </div>
        </InterneEtatStyle>
      </div>
    </InterneSectionStyle>

    <InterneSectionStyle composant="Coquille" :numero="14">
      <div class="pile">
        <InterneEtatStyle v-for="c in coquilles" :key="c.situation" :etats="c.situation">
          <CanonCoquille
            :composition="c.composition"
            :contexte="c.contexte"
            :route-active="c.composition.accueil.route"
            apercu
          >
            <div class="apercu-ecran">
              <p class="mention">{{ pack.date(demo.JOUR) }} · {{ demo.EFFECTIF }} · {{ demo.CLASSE }}</p>
            </div>
          </CanonCoquille>
        </InterneEtatStyle>
      </div>
    </InterneSectionStyle>
  </div>
</template>

<style scoped>
.page {
  max-width: 1320px;
  margin: 0 auto;
  padding: 0 16px 96px;
}
.entete {
  padding: 40px 0 24px;
}
.titre {
  margin: 0 0 8px;
  font-family: var(--font-titres);
  font-weight: 700;
  font-size: 34px;
  letter-spacing: -0.02em;
}
.intro {
  max-width: 640px;
  margin: 0;
  color: var(--text-muted);
  font-size: 16px;
}
.grille {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 16px;
}
.grille.large {
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
}
.grille.cartes {
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
}
.pile {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.rangee {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 16px;
}
.espace {
  margin-top: 20px;
}
.sous-titre {
  margin: 24px 0 8px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-muted);
}
.mention {
  margin: 0;
  font-size: 12px;
  color: var(--text-muted);
}
.identite {
  display: flex;
  flex-direction: column;
}
.nom-personne {
  font-size: 14px;
  font-weight: 500;
}
.defilement {
  width: 100%;
  overflow-x: auto;
}
.etroit {
  width: 100%;
  max-width: 358px;
}
.cadre-ruban {
  width: 100%;
  overflow: hidden;
  border: var(--filet) solid var(--border);
  border-radius: var(--rayon-carte);
}
.apercu-ecran {
  padding: 16px;
}
</style>
