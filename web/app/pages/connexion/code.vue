<script setup lang="ts">
// L'écran du code reçu (US1, artboard US1 « Le code, avec le compte à rebours » et « Les refus,
// chacun avec son versant positif »).
//
// Trois choses le gouvernent :
//   - le compte à rebours du renvoi s'affiche **avant** qu'on appuie, en attente, jamais en faute ;
//   - chaque refus dit ce qui reste ouvert : les tentatives, un code neuf, une durée de reprise ;
//   - une action impossible est absente, jamais grisée : sans code vivant, le champ n'est pas là.
//
// La carte « Le SMS n'est pas encore arrivé ? » n'affiche aucun numéro : avant la session, le
// tenant n'est pas connu, et un numéro de déploiement serait celui de l'éditeur (écart E-01).
import { ErreurApi } from '~/core/api/client'
import type { ChoixCompte, SessionOuverte } from '~/core/session/etat'
import { compteARebours, LONGUEUR_CODE, REFUS } from '~/core/session/etat'
import { etatEcranCode } from '~/core/session/ecrans'

definePageMeta({ sansCoquille: true, contexteTactile: 'standard' })

const NUMERO = '/connexion'
const PIN = '/connexion/pin'
const ACCUEIL = '/'
const TIC = 1000

const { t } = useLibelles()
const routeur = useRouter()
const { identifiant, demandeLe, delaiRenvoi, demanderCode, verifierCode } = useSession()

const saisie = ref('')
/** Les comptes que ce numéro porte, quand il en porte plusieurs (US8) : le choix, avant tout. */
const choix = ref<ChoixCompte[]>([])
const tentee = ref(false)
const refus = ref<string | null>(null)
const tentativesRestantes = ref<number | null>(null)
const occupe = ref(false)
const maintenant = ref(Date.now())
let battement: ReturnType<typeof setInterval> | undefined

/** Le numéro n'est connu que si cet écran vient de celui du numéro : il ne s'invente pas. */
const connu = computed(() => identifiant.value !== '')
/** Zéro tant qu'aucune demande n'a été faite : le rendu du serveur ne dépend d'aucune horloge. */
const secondes = computed(() =>
  demandeLe.value === 0 ? 0 : compteARebours(demandeLe.value, delaiRenvoi.value, maintenant.value),
)
const duree = computed(() => ({ duree: t('session.duree_secondes', { n: secondes.value }) }))

const ecran = computed(() =>
  etatEcranCode({
    saisie: saisie.value,
    tentee: tentee.value,
    refus: refus.value,
    tentativesRestantes: tentativesRestantes.value,
    secondes: secondes.value,
  }),
)
const champ = computed(() => ecran.value.champ && connu.value)
const action = computed(() => (champ.value ? ecran.value.action : 'nouveau'))
const libelleAction = computed(() =>
  action.value === 'ouvrir' ? 'session.code.ouvrir' : 'session.code.nouveau',
)

// Un code faux ne l'est plus dès qu'on en saisit un autre ; une attente, elle, court toujours.
watch(saisie, () => {
  if (refus.value === REFUS.codeFaux) refus.value = null
})

onMounted(() => {
  battement = setInterval(() => {
    maintenant.value = Date.now()
  }, TIC)
})
onBeforeUnmount(() => clearInterval(battement))

/** Le refus `AUT_OTP_INVALIDE` porte ce qui reste ; les autres n'ont rien à compter. */
function restantes(details: Record<string, unknown>): number | null {
  const valeur = details.tentatives_restantes
  return typeof valeur === 'number' ? valeur : null
}

/**
 * Où la session ouverte conduit : le code personnel si le compte n'en a pas encore, l'accueil
 * sinon. La navigation est un vrai chargement : les jetons vivent dans des cookies qu'aucun
 * script ne lit, et c'est le rendu du serveur qui va chercher le contexte de la session qui
 * vient de naître.
 */
function destination(session: SessionOuverte): string {
  if (session.compte.pin_defini) return ACCUEIL
  return routeur.resolve(PIN).matched.length > 0 ? PIN : ACCUEIL
}

function initiales(compte: ChoixCompte): string {
  return `${compte.prenoms[0] ?? ''}${compte.nom[0] ?? ''}`.toUpperCase()
}
function nomComplet(compte: ChoixCompte): string {
  return `${compte.prenoms} ${compte.nom}`.trim()
}

async function verifier(compteId?: string) {
  if (occupe.value) return
  tentee.value = true
  refus.value = null
  if (saisie.value.length !== LONGUEUR_CODE) return
  occupe.value = true
  try {
    const etape = await verifierCode(identifiant.value, saisie.value, compteId)
    // Le numéro porte plusieurs comptes : l'écran demande qui ouvre la session (US8).
    if (etape.nom === 'choix') choix.value = etape.comptes
    else await navigateTo(destination(etape.session), { external: true })
  } catch (echec) {
    if (!(echec instanceof ErreurApi)) throw echec
    // Le code saisi reste sous les yeux, avec ce que le refus dit de lui : c'est en le
    // comparant au dernier SMS reçu qu'on voit le chiffre qui manque.
    refus.value = echec.code
    tentativesRestantes.value = restantes(echec.details)
    tentee.value = false
  } finally {
    occupe.value = false
  }
}

/** Un code neuf : pour le numéro connu, sinon l'écran du numéro, qui est le seul à le demander. */
async function renvoyer() {
  if (occupe.value || !connu.value) {
    await navigateTo(NUMERO)
    return
  }
  occupe.value = true
  refus.value = null
  tentativesRestantes.value = null
  saisie.value = ''
  tentee.value = false
  try {
    await demanderCode(identifiant.value)
  } catch (echec) {
    if (!(echec instanceof ErreurApi)) throw echec
    refus.value = echec.code
  } finally {
    occupe.value = false
  }
}

function agir() {
  if (action.value === 'ouvrir') return verifier()
  return renvoyer()
}

/** Le compte désigné rejoue le même code : le serveur trace le choix avec l'ouverture. */
function designer(compte: ChoixCompte) {
  return verifier(compte.compte_id)
}
</script>

<template>
  <article class="code">
    <header class="barre">
      <NuxtLink :to="NUMERO" class="retour" :aria-label="t('coquille.retour')">
        <InterneIcone nom="retour" :taille="19" />
      </NuxtLink>
      <p class="barre-titre">{{ t('session.code.entete') }}</p>
    </header>

    <!-- Le code est bon, le numéro porte plusieurs comptes : qui ouvre la session ? (US8) -->
    <div v-if="choix.length" class="corps">
      <CanonAlerte niveau="enregistre" titre="session.choix.verifie" />
      <div>
        <h1 class="titre">{{ t('session.choix.titre') }}</h1>
        <p class="partage">{{ t('session.choix.partage') }}</p>
      </div>
      <ul class="comptes">
        <li v-for="compte in choix" :key="compte.compte_id">
          <button type="button" class="tuile" @click="designer(compte)">
            <CanonAvatar :initiales="initiales(compte)" :nom="nomComplet(compte)" taille="grande" />
            <span class="tuile-texte">
              <span class="tuile-nom">{{ nomComplet(compte) }}</span>
              <span class="tuile-mention">{{ compte.etablissement_nom }}</span>
            </span>
            <InterneIcone nom="chevron" :taille="18" class="tuile-chevron" />
          </button>
        </li>
      </ul>
      <p class="un-seul">{{ t('session.choix.un_seul_sms') }}</p>
    </div>

    <div v-else class="corps">
      <div>
        <h1 class="titre">{{ t('session.code.titre') }}</h1>
        <p class="envoi">
          <span v-if="connu" class="numero">{{ t('session.code.envoye_au', { numero: identifiant }) }}</span>
          <NuxtLink :to="NUMERO" class="modifier">{{ t('session.code.modifier') }}</NuxtLink>
        </p>
      </div>

      <CanonAlerte
        v-if="ecran.alerte"
        :niveau="ecran.alerte.niveau"
        :titre="ecran.alerte.titre"
        :corps="ecran.alerte.corps"
        :parametres="duree"
      />

      <form class="formulaire" novalidate @submit.prevent="agir">
        <CanonChamp
          v-if="champ"
          v-model="saisie"
          libelle="session.code.champ"
          saisie="code"
          aide="session.code.aide"
          :erreur="ecran.erreur ?? undefined"
          :parametres-erreur="ecran.parametresErreur"
        />
        <CanonBouton variante="principal" type="submit" pleine-largeur :libelle="libelleAction" />
      </form>

      <CanonAlerte
        v-if="!ecran.alerte && secondes > 0"
        niveau="attente"
        titre="session.code.renvoyer_dans"
        corps="session.code.tarde"
        :parametres="duree"
      />
      <CanonBouton
        v-else-if="champ && secondes === 0"
        variante="secondaire"
        pleine-largeur
        libelle="session.code.renvoyer"
        @appui="renvoyer"
      />

      <section class="carte">
        <h2 class="carte-titre">{{ t('session.code.pas_arrive.titre') }}</h2>
        <p class="carte-corps">{{ t('session.code.pas_arrive.corps') }}</p>
      </section>
    </div>
  </article>
</template>

<style scoped>
.code {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 420px;
  min-height: 100dvh;
  margin: 0 auto;
  background: var(--bg);
}
.barre {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 0 0 auto;
  padding: 10px 16px;
  border-bottom: var(--filet) solid var(--border);
  background: var(--surface);
}
.retour {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--cible-plancher);
  height: var(--cible-plancher);
  flex: 0 0 auto;
  border: var(--filet) solid var(--border);
  border-radius: var(--rayon-pastille);
  color: var(--text);
}
.barre-titre {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}
.corps {
  display: flex;
  flex-direction: column;
  gap: 18px;
  flex: 1;
  padding: 20px 16px 24px;
}
.titre {
  margin: 0;
  font-family: var(--font-titres);
  font-weight: 700;
  font-size: 24px;
  line-height: 1.2;
  letter-spacing: -0.02em;
}
.envoi {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin: 8px 0 0;
  font-size: 14px;
  color: var(--text-muted);
}
.numero {
  font-variant-numeric: tabular-nums;
}
.modifier {
  display: inline-flex;
  align-items: center;
  min-height: var(--cible, var(--cible-standard));
  font-weight: 600;
}
.formulaire {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.carte {
  margin-top: auto;
  padding: 14px 16px;
  border: var(--filet) solid var(--border);
  border-radius: var(--rayon-carte);
  background: var(--surface);
}
.carte-titre {
  margin: 0;
  font-family: var(--font-titres);
  font-weight: 600;
  font-size: 15px;
}
.carte-corps {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--text-muted);
}
.partage {
  margin: 8px 0 0;
  font-size: 14px;
  color: var(--text-muted);
}
.comptes {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.tuile {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  min-height: var(--cible, var(--cible-standard));
  padding: 10px 12px;
  border: var(--filet) solid var(--border);
  border-radius: var(--rayon-carte);
  background: var(--surface);
  color: var(--text);
  font-family: inherit;
  text-align: start;
  cursor: pointer;
}
.tuile:hover {
  border-color: var(--primary);
}
.tuile:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}
.tuile-texte {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}
.tuile-nom {
  font-size: 15px;
  font-weight: 500;
}
.tuile-mention {
  font-size: 13px;
  color: var(--text-muted);
}
.tuile-chevron {
  flex: 0 0 auto;
  color: var(--text-muted);
  transform: rotate(-90deg);
}
.un-seul {
  margin: auto 0 0;
  font-size: 13px;
  color: var(--text-muted);
}
</style>
