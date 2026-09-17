// Le registre des domaines que l'interface sait afficher (data-model.md § 2). Il connaît des
// domaines, des familles, leurs mots, leur ordre et leurs écrans ; il ne connaît aucun rôle.
// Un domaine absent d'ici est ignoré par la composition, et signalé en développement.
import type { CodeFamille, Domaine, Entree, Famille, IconeDomaine, Libelle } from './types'

export const FAMILLES: Famille[] = [
  { code: 'ELEVES', libelleCle: 'famille.ELEVES', ordre: 1 },
  { code: 'ENSEIGNEMENT', libelleCle: 'famille.ENSEIGNEMENT', ordre: 2 },
  { code: 'GESTION', libelleCle: 'famille.GESTION', ordre: 3 },
  { code: 'COMMUNICATION', libelleCle: 'famille.COMMUNICATION', ordre: 4 },
  { code: 'PARAMETRES', libelleCle: 'famille.PARAMETRES', ordre: 5 },
]

type ModeleEntree = Omit<Entree, 'compte'>

interface ModeleDomaine {
  code: string
  libelle: Libelle
  famille: CodeFamille
  icone: IconeDomaine
  /** Pour chaque objet de capacité (le deuxième segment), les écrans qu'il ouvre. */
  ecrans: Record<string, ModeleEntree[]>
}

const route = (domaine: string, vue?: string) => `/d/${domaine}${vue ? `?vue=${vue}` : ''}`
const ecran = (domaine: string, code: string, icone: IconeDomaine, vue?: string): ModeleEntree => ({
  code,
  libelle: { cle: `entree.${code}` },
  route: route(domaine, vue),
  icone,
})

const MODELES: ModeleDomaine[] = [
  {
    code: 'scolarite',
    libelle: { cle: 'domaine.scolarite' },
    famille: 'ELEVES',
    icone: 'inscription',
    ecrans: { inscription: [ecran('scolarite', 'inscriptions', 'inscription')] },
  },
  {
    code: 'vie_scolaire',
    libelle: { cle: 'domaine.vie_scolaire' },
    famille: 'ELEVES',
    icone: 'appel',
    ecrans: {
      appel: [
        ecran('vie_scolaire', 'appel_du_jour', 'appel'),
        ecran('vie_scolaire', 'absences', 'horloge', 'absences'),
      ],
      sanction: [ecran('vie_scolaire', 'sanctions', 'sanction', 'sanctions')],
    },
  },
  {
    code: 'pedagogie',
    libelle: { cle: 'domaine.pedagogie' },
    famille: 'ENSEIGNEMENT',
    icone: 'progression',
    ecrans: {
      edt: [ecran('pedagogie', 'emploi_du_temps', 'progression')],
      progression: [ecran('pedagogie', 'progressions', 'progression', 'progressions')],
    },
  },
  {
    code: 'evaluation',
    libelle: { cle: 'domaine.evaluation' },
    famille: 'ENSEIGNEMENT',
    icone: 'evaluation',
    ecrans: {
      note: [ecran('evaluation', 'notes', 'evaluation')],
      bulletin: [ecran('evaluation', 'bulletins', 'evaluation', 'bulletins')],
    },
  },
  {
    code: 'conseil',
    libelle: { code: 'CONSEIL_CLASSE' },
    famille: 'ENSEIGNEMENT',
    icone: 'conseil',
    ecrans: { decision: [ecran('conseil', 'decisions', 'conseil')] },
  },
  {
    code: 'finance',
    libelle: { cle: 'domaine.finance' },
    famille: 'GESTION',
    icone: 'finance',
    ecrans: { encaissement: [ecran('finance', 'encaissements', 'finance')] },
  },
  {
    code: 'personnel',
    libelle: { cle: 'domaine.personnel' },
    famille: 'GESTION',
    icone: 'personnel',
    ecrans: {},
  },
  {
    code: 'communication',
    libelle: { cle: 'domaine.communication' },
    famille: 'COMMUNICATION',
    icone: 'message',
    ecrans: { circulaire: [ecran('communication', 'circulaires', 'message')] },
  },
  {
    code: 'tenant',
    libelle: { cle: 'domaine.tenant' },
    famille: 'PARAMETRES',
    icone: 'reglage',
    ecrans: {},
  },
]

export interface EntreeRegistre extends ModeleDomaine {
  ordre: number
  route: string
}

export const DOMAINES: EntreeRegistre[] = MODELES.map((m, i) => ({ ...m, ordre: i + 1, route: route(m.code) }))

/** Le domaine prêt à afficher, pour les objets de capacité que la personne détient. */
export function instancier(modele: EntreeRegistre, objets: Set<string>): Domaine {
  const vues = new Map<string, Entree>()
  for (const [objet, ecrans] of Object.entries(modele.ecrans)) {
    if (!objets.has(objet)) continue
    for (const e of ecrans) vues.set(e.code, { ...e, compte: null })
  }
  if (vues.size === 0) {
    vues.set(modele.code, { code: modele.code, libelle: modele.libelle, route: modele.route, icone: modele.icone, compte: null })
  }
  return {
    code: modele.code,
    libelle: modele.libelle,
    famille: modele.famille,
    ordre: modele.ordre,
    route: modele.route,
    icone: modele.icone,
    compte: null,
    entrees: [...vues.values()],
  }
}
