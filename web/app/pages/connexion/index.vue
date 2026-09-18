<script setup lang="ts">
// L'écran qui ouvre une session (US1 et US3, artboards US1 et US3). Il porte deux parcours, et
// c'est l'appareil qui décide lequel s'affiche d'abord :
//
//   - l'appareil est connu d'au moins un compte : on propose **son nom** et quatre chiffres,
//     jamais son numéro (FR-021) ; aucun message ne part ;
//   - sinon, ou sur demande : le numéro, puis le code reçu par SMS.
//
// Avant la session, le tenant n'est pas connu : l'écran porte le nom du produit, jamais celui
// d'un établissement (écart E-01), et l'indicatif proposé vient du déploiement (research.md R-14).
//
// La vérification de forme faite ici est de présentation : elle évite d'envoyer un SMS pour une
// saisie manifestement inachevée. Le serveur reste seul juge du numéro, et sa réponse est la même
// que le numéro soit connu ou non : aucun écran ne dit qu'un numéro est inconnu.
import { ErreurApi } from '~/core/api/client'
import { NOM } from '~/core/produit'
import type { CompteConnu } from '~/core/session/etat'
import { estMotif, REFUS } from '~/core/session/etat'
import {
  etatEcranNumero,
  etatEcranOuverture,
  formePin,
  formePlausible,
  identifiant,
} from '~/core/session/ecrans'
import type { Langue } from '~/core/i18n/libelles'
import { LANGUES } from '~/core/i18n/libelles'

definePageMeta({ sansCoquille: true, contexteTactile: 'standard' })

const CODE = '/connexion/code'
const ACCUEIL = '/'

const route = useRoute()
const { t, langue, changer } = useLibelles()
const { demanderCode, comptesDeLAppareil, ouvrirParPin } = useSession()
const indicatif = useRuntimeConfig().public.indicatifDefaut

/**
 * Les comptes que cet appareil connaît (research.md R-20). La demande part du **navigateur** :
 * le cookie des secrets d'appareil est borné au chemin de l'authentification, et le rendu du
 * serveur, qui reçoit les cookies de la page, ne le voit donc jamais. Un refus n'est pas une
 * panne : l'écran retombe sur le parcours par SMS, qui marche toujours.
 *
 * Tant que la réponse n'est pas là, aucun des deux parcours ne s'affiche : montrer le numéro
 * pour le remplacer aussitôt par un nom serait un écran qui se dédit.
 */
const { data: connus } = await useAsyncData<CompteConnu[]>(
  'comptes-appareil',
  async () => {
    try {
      return await comptesDeLAppareil()
    } catch {
      return []
    }
  },
  { server: false },
)
/** Les comptes que l'appareil a oubliés en cours de route (compte suspendu, secret périmé). */
const oublies = ref<string[]>([])
const comptes = computed(() => (connus.value ?? []).filter((c) => !oublies.value.includes(c.compte_id)))
/** Le navigateur n'a pas encore répondu : l'écran attend, il ne devine pas. */
const enAttente = computed(() => connus.value === null)

/** Le motif d'une session finie, quand la fermeture ou une révocation nous amène ici (E-07). */
const motif = computed(() => (estMotif(route.query.motif) ? route.query.motif : null))

// Le numéro : ce que l'écran demande quand aucun compte n'est connu, ou sur demande.
const parSms = ref(false)
const saisie = ref('')
const tentee = ref(false)
const refus = ref<string | null>(null)
const envoi = ref(false)

// Le code personnel : le compte choisi parmi ceux que l'appareil connaît, et ses quatre chiffres.
const choisi = ref<string | null>(null)
const pin = ref('')
const refusPin = ref<string | null>(null)
const tentativesRestantes = ref<number | null>(null)
const ouverture = ref(false)

const parPin = computed(() => !parSms.value && comptes.value.length > 0)
const compte = computed(() => comptes.value.find((c) => c.compte_id === choisi.value) ?? null)
/** Un seul compte connu : son nom s'affiche sans qu'on ait à le désigner. */
const unique = computed(() => (comptes.value.length === 1 ? comptes.value[0]! : null))
const actif = computed(() => compte.value ?? unique.value)

const ecran = computed(() =>
  etatEcranNumero({ saisie: saisie.value, tentee: tentee.value, refus: refus.value }),
)
const ecranPin = computed(() =>
  etatEcranOuverture({ refus: refusPin.value, tentativesRestantes: tentativesRestantes.value }),
)
const initiale = computed(() => NOM.slice(0, 1))

function initiales(connu: CompteConnu): string {
  return `${connu.prenoms[0] ?? ''}${connu.nom[0] ?? ''}`.toUpperCase()
}
function nomComplet(connu: CompteConnu): string {
  return `${connu.prenoms} ${connu.nom}`.trim()
}

// Le refus du serveur porte sur le numéro qu'on lui a envoyé : dès qu'il change, il ne vaut
// plus. La vérification de forme, elle, reste vive une fois l'envoi tenté : c'est ce que
// l'artboard montre, un format annoncé pendant la saisie.
watch(saisie, () => {
  refus.value = null
})
// Un code personnel faux ne l'est plus dès qu'on en saisit un autre ; un verrou, lui, tient.
watch(pin, () => {
  if (refusPin.value === REFUS.pinFaux) refusPin.value = null
})
// La langue se choisit avant toute session, dans son propre nom (US4, scénario 7).
const LIBELLE_LANGUE: Record<Langue, string> = { fr: 'session.langue.fr', en: 'session.langue.en' }

/** Le parcours par SMS, depuis l'écran du code personnel : c'est lui qui débloque tout. */
function versSms() {
  parSms.value = true
}

function designer(connu: CompteConnu) {
  choisi.value = connu.compte_id
  pin.value = ''
  refusPin.value = null
  tentativesRestantes.value = null
  // Un compte sans code personnel ne peut ouvrir que par SMS : l'écran le conduit, il ne le grise pas.
  if (!connu.pin_defini) versSms()
}

async function envoyer() {
  if (envoi.value) return
  tentee.value = true
  refus.value = null
  if (!formePlausible(saisie.value)) return
  envoi.value = true
  try {
    await demanderCode(identifiant(indicatif, saisie.value))
    await navigateTo(CODE)
  } catch (echec) {
    // Un refus du serveur se dit sur cet écran ; une limite de débit, elle, mène à l'écran du
    // code, où le compte à rebours court et où le dernier code reçu vaut encore.
    if (!(echec instanceof ErreurApi)) throw echec
    refus.value = echec.code
    if (echec.code === REFUS.limiteDebit) await navigateTo(CODE)
  } finally {
    envoi.value = false
  }
}

/** Ce qu'un refus porte de compté : les essais qui restent, et rien d'autre. */
function restants(details: Record<string, unknown>): number | null {
  const valeur = details.tentatives_restantes
  return typeof valeur === 'number' ? valeur : null
}

async function ouvrir() {
  const connu = actif.value
  if (ouverture.value || !connu || !formePin(pin.value)) return
  ouverture.value = true
  refusPin.value = null
  try {
    await ouvrirParPin(connu.compte_id, pin.value)
    // Un vrai chargement : c'est le rendu du serveur qui va chercher le contexte de la session.
    await navigateTo(ACCUEIL, { external: true })
  } catch (echec) {
    if (!(echec instanceof ErreurApi)) throw echec
    refusPin.value = echec.code
    tentativesRestantes.value = restants(echec.details)
    pin.value = ''
    // Le serveur a fait oublier ce compte à l'appareil : l'écran cesse de le proposer.
    if (etatEcranOuverture({ refus: echec.code, tentativesRestantes: null }).oublier) {
      oublies.value = [...oublies.value, connu.compte_id]
      choisi.value = null
    }
  } finally {
    ouverture.value = false
  }
}
</script>

<template>
  <article class="connexion">
    <div class="langues" role="group" :aria-label="t('coquille.langue')">
      <button
        v-for="code in LANGUES"
        :key="code"
        type="button"
        class="langue"
        :lang="code"
        :aria-pressed="code === langue"
        @click="changer(code)"
      >
        {{ t(LIBELLE_LANGUE[code]) }}
      </button>
    </div>

    <CanonAlerte
      v-if="motif"
      niveau="information"
      :titre="`session.${motif}.titre`"
      :corps="`session.${motif}.corps`"
    />

    <!-- L'appareil n'a pas encore dit ce qu'il connaît : le produit se nomme, et rien de plus. -->
    <template v-if="enAttente">
      <header class="entete">
        <span class="marque" aria-hidden="true">{{ initiale }}</span>
        <p class="produit">{{ NOM }}</p>
        <p class="attente" aria-live="polite">{{ t('session.ouverture.instant') }}</p>
      </header>
    </template>

    <!-- L'appareil connaît plusieurs comptes : qui ouvre la session ? -->
    <template v-else-if="parPin && !actif">
      <header class="entete">
        <h1 class="titre">{{ t('session.ouverture.qui') }}</h1>
        <p class="sous-titre">{{ t('session.ouverture.poste') }}</p>
      </header>
      <ul class="comptes">
        <li v-for="connu in comptes" :key="connu.compte_id">
          <button type="button" class="tuile" @click="designer(connu)">
            <CanonAvatar :initiales="initiales(connu)" :nom="nomComplet(connu)" taille="grande" />
            <span class="tuile-texte">
              <span class="tuile-nom">{{ nomComplet(connu) }}</span>
              <span class="tuile-mention">
                {{ t(connu.pin_defini ? 'session.ouverture.pin_defini' : 'session.ouverture.pin_absent') }}
              </span>
            </span>
            <InterneIcone nom="chevron" :taille="18" class="tuile-chevron" />
          </button>
        </li>
      </ul>
      <p class="autre">
        <CanonBouton variante="discret" libelle="session.ouverture.autre_numero" @appui="versSms" />
      </p>
    </template>

    <!-- L'appareil connaît ce compte : son nom, et quatre chiffres. -->
    <template v-else-if="parPin && actif">
      <header class="entete">
        <CanonAvatar :initiales="initiales(actif)" :nom="nomComplet(actif)" taille="grande" />
        <p class="bonjour">{{ t('session.ouverture.bonjour') }}</p>
        <h1 class="titre">{{ nomComplet(actif) }}</h1>
      </header>

      <CanonAlerte
        v-if="ecranPin.alerte"
        :niveau="ecranPin.alerte.niveau"
        :titre="ecranPin.alerte.titre"
        :corps="ecranPin.alerte.corps"
      />

      <form v-if="ecranPin.champ" class="formulaire" novalidate @submit.prevent="ouvrir">
        <CanonChamp
          v-model="pin"
          libelle="session.ouverture.champ"
          saisie="code"
          aide="session.ouverture.aide"
          :erreur="ecranPin.erreur ?? undefined"
          :parametres-erreur="ecranPin.parametresErreur"
        />
        <CanonBouton
          variante="principal"
          type="submit"
          pleine-largeur
          libelle="session.ouverture.ouvrir"
        />
      </form>

      <div class="issues">
        <CanonBouton
          v-if="!ecranPin.champ"
          variante="principal"
          pleine-largeur
          libelle="session.ouverture.par_sms"
          @appui="versSms"
        >
          <template #icone><InterneIcone nom="message" :taille="18" /></template>
        </CanonBouton>
        <CanonBouton
          v-else
          variante="discret"
          libelle="session.ouverture.oublie"
          @appui="versSms"
        />
        <CanonBouton
          v-if="comptes.length > 1"
          variante="discret"
          libelle="session.ouverture.autre_compte"
          @appui="choisi = null"
        />
        <CanonBouton variante="discret" libelle="session.ouverture.pas_vous" @appui="versSms" />
      </div>
    </template>

    <!-- Le numéro : le parcours qui marche partout, sur tout appareil. -->
    <template v-else>
      <header class="entete">
        <span class="marque" aria-hidden="true">{{ initiale }}</span>
        <p class="produit">{{ NOM }}</p>
        <h1 class="titre">{{ t('session.numero.titre') }}</h1>
        <p class="sous-titre">{{ t('session.numero.sous_titre') }}</p>
      </header>

      <form class="formulaire" novalidate @submit.prevent="envoyer">
        <div class="numero">
          <p v-if="indicatif" class="indicatif">
            <span class="etiquette">{{ t('session.numero.indicatif') }}</span>
            <span class="valeur">{{ indicatif }}</span>
          </p>
          <CanonChamp
            v-model="saisie"
            class="champ-numero"
            libelle="session.numero.champ"
            saisie="code"
            aide="session.numero.aide"
            :erreur="ecran.erreur ?? undefined"
          />
        </div>
        <div class="action">
          <CanonBouton
            variante="principal"
            type="submit"
            pleine-largeur
            libelle="session.numero.action"
          >
            <template #icone><InterneIcone nom="message" :taille="18" /></template>
          </CanonBouton>
          <p class="gratuit">{{ t('session.numero.sms_gratuit') }}</p>
        </div>
      </form>
    </template>
  </article>
</template>

<style scoped>
.connexion {
  display: flex;
  flex-direction: column;
  gap: 22px;
  width: 100%;
  max-width: 420px;
  min-height: 100dvh;
  margin: 0 auto;
  padding: 16px 16px 24px;
  background: var(--bg);
}
.langues {
  display: flex;
  align-self: flex-end;
  overflow: hidden;
  border: var(--filet) solid var(--border-strong);
  border-radius: var(--rayon-champ);
}
.langue {
  min-width: var(--cible-plancher);
  min-height: var(--cible, var(--cible-standard));
  padding: 0 12px;
  border: 0;
  background: var(--surface);
  color: var(--text-muted);
  font-family: inherit;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
}
.langue[aria-pressed='true'] {
  background: var(--primary);
  color: var(--primary-ink);
  font-weight: 600;
}
.marque {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: var(--rayon-carte);
  background: var(--primary);
  color: var(--primary-ink);
  font-family: var(--font-titres);
  font-weight: 700;
  font-size: 16px;
}
.produit {
  margin: 10px 0 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-muted);
}
.attente {
  margin: 10px 0 0;
  font-size: 14px;
  color: var(--text-muted);
}
.bonjour {
  margin: 10px 0 0;
  font-size: 14px;
  color: var(--text-muted);
}
.titre {
  margin: 6px 0 0;
  font-family: var(--font-titres);
  font-weight: 700;
  font-size: 26px;
  line-height: 1.2;
  letter-spacing: -0.02em;
}
.sous-titre {
  margin: 8px 0 0;
  font-size: 14px;
  color: var(--text-muted);
}
.formulaire {
  display: flex;
  flex-direction: column;
  gap: 22px;
}
.numero {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}
.indicatif {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin: 0;
  flex: 0 0 auto;
}
.indicatif .etiquette {
  font-size: 13px;
  font-weight: 500;
}
.indicatif .valeur {
  display: flex;
  align-items: center;
  min-height: var(--cible, var(--cible-standard));
  padding: 0 12px;
  border-radius: var(--rayon-champ);
  background: var(--surface-sunken);
  font-family: var(--font-mono);
  font-weight: 500;
  font-size: 15px;
  font-variant-numeric: tabular-nums;
}
.champ-numero {
  flex: 1;
}
.action {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: auto;
}
.gratuit {
  margin: 0;
  font-size: 12px;
  color: var(--text-muted);
  text-align: center;
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
.tuile:focus-visible,
.langue:focus-visible {
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
.issues {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  margin-top: auto;
}
.autre {
  display: flex;
  justify-content: center;
  margin: auto 0 0;
}
</style>
