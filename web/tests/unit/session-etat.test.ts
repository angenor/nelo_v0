// US1 : ce que la réponse du serveur commande aux deux écrans de la connexion, en fonctions
// pures. Aucune règle métier n'est rejouée ici : on vérifie que chaque refus se traduit en un
// écran qui dit son versant positif, et qu'une action impossible est absente, jamais grisée.
import { describe, expect, it } from 'vitest'
import fr from '../../app/core/i18n/fr.json'
import type { ReponseVerification } from '../../app/core/session/etat'
import {
  compteARebours,
  DELAI_RENVOI,
  etapeSuivante,
  LONGUEUR_CODE,
  REFUS,
} from '../../app/core/session/etat'
import type { EntreeEcranCode } from '../../app/core/session/ecrans'
import {
  chiffres,
  etatEcranCode,
  etatEcranNumero,
  formePlausible,
  identifiant,
} from '../../app/core/session/ecrans'

const CLES = fr as Record<string, string>

const SESSION: ReponseVerification = {
  resultat: 'SESSION',
  jeton_acces: 'jamais-lu-par-un-script',
  expire_dans: 3600,
  appareil_connu: false,
  compte: { id: 'c1', nom: 'Traoré', prenoms: 'Awa', langue: 'fr', pin_defini: false },
}

const CHOIX: ReponseVerification = {
  resultat: 'CHOIX',
  comptes: [
    { compte_id: 'c1', nom: 'Traoré', prenoms: 'Awa', etablissement_nom: 'A' },
    { compte_id: 'c2', nom: 'Traoré', prenoms: 'Koffi', etablissement_nom: 'B' },
  ],
}

function ecranCode(entree: Partial<EntreeEcranCode> = {}) {
  return etatEcranCode({
    saisie: '',
    tentee: false,
    refus: null,
    tentativesRestantes: null,
    secondes: 0,
    ...entree,
  })
}

describe('etapeSuivante', () => {
  it('lit le résultat, jamais la forme de la réponse', () => {
    const etape = etapeSuivante(SESSION)
    expect(etape.nom).toBe('session')
    expect(etape.nom === 'session' && etape.session.compte.pin_defini).toBe(false)
  })

  it('rend le choix quand le numéro porte plusieurs comptes', () => {
    const etape = etapeSuivante(CHOIX)
    expect(etape.nom).toBe('choix')
    expect(etape.nom === 'choix' && etape.comptes).toHaveLength(2)
  })
})

describe('compteARebours', () => {
  it('rend les secondes qui restent, arrondies au haut', () => {
    expect(compteARebours(1_000, DELAI_RENVOI, 1_000 + 13_400)).toBe(47)
  })

  it('ne descend jamais sous zéro', () => {
    expect(compteARebours(0, DELAI_RENVOI, 60_000)).toBe(0)
    expect(compteARebours(0, DELAI_RENVOI, 900_000)).toBe(0)
  })

  it('compte la durée que le refus de débit a dite, pas une autre', () => {
    expect(compteARebours(0, 12, 2_000)).toBe(10)
  })
})

describe('la forme du numéro, de présentation seulement', () => {
  it('accepte les séparateurs d’usage et compte les chiffres', () => {
    expect(chiffres('07 08 12 34 56')).toBe(10)
    expect(formePlausible('07 08 12 34 56')).toBe(true)
    expect(formePlausible('+225 07-08.12')).toBe(true)
  })

  it('refuse une saisie inachevée ou impossible', () => {
    expect(formePlausible('07 08')).toBe(false)
    expect(formePlausible('appelez-moi')).toBe(false)
  })

  it('n’annonce le refus qu’au caractère impossible ou à la tentative', () => {
    expect(etatEcranNumero({ saisie: '07 08', tentee: false, refus: null }).erreur).toBeNull()
    expect(etatEcranNumero({ saisie: '07 08', tentee: true, refus: null }).erreur).toBe('session.numero.format')
    expect(etatEcranNumero({ saisie: '07 a', tentee: false, refus: null }).erreur).toBe('session.numero.format')
  })

  it('porte le refus du serveur, qui reste seul juge', () => {
    const ecran = etatEcranNumero({ saisie: '07 08 12 34 56', tentee: true, refus: REFUS.numeroInvalide })
    expect(ecran.erreur).toBe('session.numero.format')
  })

  it('compose l’identifiant avec l’indicatif affiché, sauf si la personne écrit le sien', () => {
    expect(identifiant('+225', ' 07 08 12 34 56 ')).toBe('+225 07 08 12 34 56')
    expect(identifiant('+225', '+233 07 08 12 34 56')).toBe('+233 07 08 12 34 56')
    expect(identifiant('', '07 08 12 34 56')).toBe('07 08 12 34 56')
  })
})

describe('l’écran du code', () => {
  it('au repos, montre le champ et ouvre la session', () => {
    const ecran = ecranCode()
    expect(ecran).toMatchObject({ champ: true, erreur: null, alerte: null, action: 'ouvrir' })
  })

  it('dit les tentatives qui restent sur un code faux', () => {
    const ecran = ecranCode({ refus: REFUS.codeFaux, tentativesRestantes: 3 })
    expect(ecran.erreur).toBe('session.code.tentatives_restantes')
    expect(ecran.parametresErreur).toEqual({ n: 3 })
    expect(ecran.champ).toBe(true)
  })

  it('sur un code expiré ou détruit, retire le champ et propose un code neuf', () => {
    for (const [refus, titre] of [
      [REFUS.codeExpire, 'session.code.expire'],
      [REFUS.codeEpuise, 'session.code.epuise'],
    ] as const) {
      const ecran = ecranCode({ refus })
      expect(ecran.champ, refus).toBe(false)
      expect(ecran.action, refus).toBe('nouveau')
      expect(ecran.alerte, refus).toEqual({ niveau: 'information', titre, corps: `${titre}_corps` })
    }
  })

  it('dit la limite de débit en attente, et garde le champ : le dernier code vaut encore', () => {
    const ecran = ecranCode({ refus: REFUS.limiteDebit, secondes: 47 })
    expect(ecran.alerte?.niveau).toBe('attente')
    expect(ecran.alerte?.titre).toBe('session.code.trop_de_demandes')
    expect(ecran.champ).toBe(true)
    expect(ecran.action).toBe('ouvrir')
    expect(ecran.secondes).toBe(47)
  })

  it('annonce la longueur attendue quand la vérification est tentée trop tôt', () => {
    expect(ecranCode({ saisie: '417', tentee: true }).erreur).toBe('session.code.format')
    expect(ecranCode({ saisie: '417306', tentee: true }).erreur).toBeNull()
    expect('417306'.length).toBe(LONGUEUR_CODE)
  })

  it('ne parle pas à la place d’un refus qu’il ne connaît pas', () => {
    const ecran = ecranCode({ refus: 'AUT_COMPTE_SUSPENDU' })
    expect(ecran.alerte).toBeNull()
    expect(ecran.erreur).toBeNull()
  })
})

describe('les mots des deux écrans', () => {
  it('existent tous, et chaque refus porte son versant positif', () => {
    const cles = [
      'session.numero.format',
      'session.code.format',
      'session.code.tentatives_restantes',
      'session.code.expire_corps',
      'session.code.epuise_corps',
      'session.code.trop_de_demandes_corps',
      'session.code.pas_arrive.corps',
    ]
    for (const cle of cles) expect(CLES[cle], cle).toBeTruthy()
    // E-01 : avant la session, le tenant n'est pas connu ; la carte n'affiche aucun numéro.
    expect(CLES['session.code.pas_arrive.corps']).not.toMatch(/\d/)
  })
})
