<script setup lang="ts">
// Changer son numéro, depuis son espace (US7, artboard US7). Trois temps, un seul écran :
// le nouveau numéro, le code reçu sur ce nouveau numéro, puis la confirmation.
//
// Deux règles gouvernent l'écran :
//   - l'identifiant ne change qu'à la vérification : l'ancien numéro reste valable jusque-là,
//     et l'aide le dit **avant** le geste ;
//   - rien, avant la vérification, ne dit qu'un numéro est déjà pris (écart E-04) : le refus
//     `AUT_IDENTIFIANT_DEJA_UTILISE` arrive au retour du code, avec son versant positif.
//
// Le numéro actuel ne s'affiche nulle part : le contexte ne le porte pas (03-api.md § 1.9), et
// l'inventer serait une seconde vérité. L'avertissement suffit à dire ce qui va se passer.
//
// L'écran est atteint depuis le menu de compte de l'en-tête : le profil arrive avec T3a.
import { ErreurApi } from '~/core/api/client'
import { compteARebours, LONGUEUR_CODE, REFUS } from '~/core/session/etat'
import { formePlausible, identifiant } from '~/core/session/ecrans'

definePageMeta({ contexteTactile: 'standard' })

const TIC = 1000

const { t } = useLibelles()
const {
  demandeLe,
  delaiRenvoi,
  demanderChangementTelephone,
  verifierChangementTelephone,
} = useSession()
const indicatif = useRuntimeConfig().public.indicatifDefaut

/** Le temps de l'écran : le numéro, le code reçu dessus, puis ce qui a changé. */
type Temps = 'numero' | 'code' | 'change'
const temps = ref<Temps>('numero')

const numero = ref('')
const code = ref('')
const nouveau = ref('')
const tentee = ref(false)
const refus = ref<string | null>(null)
const occupe = ref(false)
const maintenant = ref(Date.now())
let battement: ReturnType<typeof setInterval> | undefined

const secondes = computed(() =>
  demandeLe.value === 0 ? 0 : compteARebours(demandeLe.value, delaiRenvoi.value, maintenant.value),
)
const duree = computed(() => ({ duree: t('session.duree_secondes', { n: secondes.value }) }))

/** Le refus du numéro, dit dans son champ : la forme, ou l'identifiant déjà porté (E-04). */
const erreurNumero = computed(() => {
  if (refus.value === REFUS.identifiantPris) return 'session.telephone.deja_utilise'
  if (refus.value === REFUS.numeroInvalide) return 'session.numero.format'
  if (tentee.value && !formePlausible(numero.value)) return 'session.numero.format'
  return undefined
})
/** Le refus du code, dit dans son champ, avec ce qui reste ouvert. */
const erreurCode = computed(() => {
  if (refus.value === REFUS.codeFaux) return 'session.telephone.code_faux'
  if (refus.value === REFUS.codeExpire || refus.value === REFUS.codeEpuise) {
    return 'session.telephone.code_mort'
  }
  if (tentee.value && code.value.length !== LONGUEUR_CODE) return 'session.code.format'
  return undefined
})

watch(numero, () => {
  refus.value = null
})
watch(code, () => {
  refus.value = null
})

onMounted(() => {
  battement = setInterval(() => {
    maintenant.value = Date.now()
  }, TIC)
})
onBeforeUnmount(() => clearInterval(battement))

async function demander() {
  if (occupe.value) return
  tentee.value = true
  refus.value = null
  if (!formePlausible(numero.value)) return
  occupe.value = true
  const cible = identifiant(indicatif, numero.value)
  try {
    await demanderChangementTelephone(cible)
    nouveau.value = cible
    code.value = ''
    tentee.value = false
    temps.value = 'code'
  } catch (echec) {
    if (!(echec instanceof ErreurApi)) throw echec
    refus.value = echec.code
  } finally {
    occupe.value = false
  }
}

async function confirmer() {
  if (occupe.value) return
  tentee.value = true
  refus.value = null
  if (code.value.length !== LONGUEUR_CODE) return
  occupe.value = true
  try {
    await verifierChangementTelephone(code.value)
    temps.value = 'change'
  } catch (echec) {
    if (!(echec instanceof ErreurApi)) throw echec
    refus.value = echec.code
    tentee.value = false
    // Le numéro est déjà celui d'un autre compte : le refus se dit là où le numéro se saisit.
    if (echec.code === REFUS.identifiantPris) temps.value = 'numero'
  } finally {
    occupe.value = false
  }
}
</script>

<template>
  <section class="telephone">
    <header>
      <h1 class="titre">{{ t('session.telephone.titre') }}</h1>
    </header>

    <!-- Le nouveau numéro. L'ancien reste l'identifiant jusqu'à la vérification. -->
    <form v-if="temps === 'numero'" class="carte" novalidate @submit.prevent="demander">
      <CanonAlerte
        niveau="information"
        titre="session.telephone.actuel"
        corps="session.telephone.actuel_informe"
      />
      <div class="numero">
        <p v-if="indicatif" class="indicatif">
          <span class="etiquette">{{ t('session.numero.indicatif') }}</span>
          <span class="valeur">{{ indicatif }}</span>
        </p>
        <CanonChamp
          v-model="numero"
          class="champ-numero"
          libelle="session.telephone.nouveau"
          saisie="code"
          aide="session.telephone.aide"
          :erreur="erreurNumero"
        />
      </div>
      <CanonBouton
        variante="principal"
        type="submit"
        pleine-largeur
        libelle="session.telephone.action"
      >
        <template #icone><InterneIcone nom="message" :taille="18" /></template>
      </CanonBouton>
    </form>

    <!-- Le code reçu sur le nouveau numéro : les mêmes règles qu'à l'ouverture. -->
    <form v-else-if="temps === 'code'" class="carte" novalidate @submit.prevent="confirmer">
      <div>
        <h2 class="sous-titre">{{ t('session.telephone.code_titre') }}</h2>
        <p class="envoi">
          <span class="valeur">{{ t('session.code.envoye_au', { numero: nouveau }) }}</span>
          <button type="button" class="modifier" @click="temps = 'numero'">
            {{ t('session.code.modifier') }}
          </button>
        </p>
      </div>
      <CanonChamp
        v-model="code"
        libelle="session.code.champ"
        saisie="code"
        aide="session.telephone.code_aide"
        :erreur="erreurCode"
      />
      <CanonBouton
        variante="principal"
        type="submit"
        pleine-largeur
        libelle="session.telephone.confirmer"
      />
      <CanonAlerte
        v-if="secondes > 0"
        niveau="attente"
        titre="session.code.renvoyer_dans"
        corps="session.telephone.tarde"
        :parametres="duree"
      />
    </form>

    <!-- Le numéro est changé : la session survit, et l'ancien numéro a été informé. -->
    <div v-else class="carte">
      <CanonAlerte
        niveau="enregistre"
        titre="session.telephone.change"
        corps="session.telephone.change_corps"
        :parametres="{ numero: nouveau }"
      />
      <p class="actuel">
        <span class="etiquette">{{ t('session.telephone.votre_numero') }}</span>
        <span class="valeur">{{ nouveau }}</span>
      </p>
    </div>
  </section>
</template>

<style scoped>
.telephone {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
  max-width: 560px;
  margin: 0 auto;
  padding: 20px 16px 24px;
}
.titre {
  margin: 0;
  font-family: var(--font-titres);
  font-weight: 700;
  font-size: 22px;
  line-height: 1.2;
  letter-spacing: -0.02em;
}
.sous-titre {
  margin: 0;
  font-family: var(--font-titres);
  font-weight: 600;
  font-size: 16px;
}
.carte {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 16px;
  border: var(--filet) solid var(--border);
  border-radius: var(--rayon-carte);
  background: var(--surface);
}
.actuel {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin: 0;
}
.etiquette {
  font-size: 13px;
  font-weight: 500;
}
.mention {
  font-size: 13px;
  color: var(--text-muted);
}
.valeur {
  font-family: var(--font-mono);
  font-weight: 500;
  font-size: 15px;
  font-variant-numeric: tabular-nums;
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
.indicatif .valeur {
  display: flex;
  align-items: center;
  min-height: var(--cible, var(--cible-standard));
  padding: 0 12px;
  border-radius: var(--rayon-champ);
  background: var(--surface-sunken);
}
.champ-numero {
  flex: 1;
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
.modifier {
  display: inline-flex;
  align-items: center;
  min-height: var(--cible, var(--cible-standard));
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--primary);
  font-family: inherit;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}
.modifier:hover {
  color: var(--primary-hover);
  text-decoration: underline;
}
.modifier:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}
</style>
