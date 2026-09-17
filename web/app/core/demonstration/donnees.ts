// Les données de démonstration des composants : le primaire, CM2 A, un maître titulaire.
// Noms fictifs, établissement fictif, jamais une donnée réelle (research.md R-18). Les formats
// sont ceux du contrat (03-api.md § 1.4) : montants entiers d'unité mineure, notes en chaîne
// décimale, dates ISO. L'interface les met en forme, elle ne les calcule pas.
import type { Canal, CodeEtat } from '../composants/etats'

export interface EleveDemonstration {
  id: string
  initiales: string
  nom: string
  matricule: string
  classe: string
  resteAPayer: number
  etat: CodeEtat
  canal: Canal
  dernierContact: string
}

export const JOUR = '2026-08-18'
export const CLASSE = 'CM2 A'
export const EFFECTIF = 34
export const TITULAIRE = 'Mme Aline Kacou'
export const SEANCE = '8h00'
export const COUT_SMS = 12

export const ELEVES: EleveDemonstration[] = [
  {
    id: 'e1',
    initiales: 'KA',
    nom: 'Koffi Aya Estelle',
    matricule: 'ELV-2026-0413',
    classe: 'CM2-A',
    resteAPayer: 0,
    etat: 'PAYE',
    canal: 'SMS',
    dernierContact: '2026-08-12',
  },
  {
    id: 'e2',
    initiales: 'BO',
    nom: 'Bamba Ousmane',
    matricule: 'ELV-2026-0301',
    classe: 'CM2-A',
    resteAPayer: 145000,
    etat: 'ECHEANCE_PROCHE',
    canal: 'WHATSAPP',
    dernierContact: '2026-08-09',
  },
  {
    id: 'e3',
    initiales: 'YS',
    nom: 'Yao Serge Emmanuel',
    matricule: 'ELV-2026-0742',
    classe: 'CM2-A',
    resteAPayer: 310000,
    etat: 'IMPAYE',
    canal: 'PAPIER',
    dernierContact: '2026-07-28',
  },
  {
    id: 'e4',
    initiales: 'DF',
    nom: 'Diabaté Fatoumata',
    matricule: 'ELV-2026-0517',
    classe: 'CM2-A',
    resteAPayer: 0,
    etat: 'SOLDE',
    canal: 'EN_LIGNE',
    dernierContact: '2026-08-14',
  },
]

export const RESULTATS_RECHERCHE = [
  { id: 'e1', initiales: 'KA', nom: 'Koffi Aya Estelle', matricule: 'ELV-2026-0413' },
  { id: 'e5', initiales: 'KM', nom: 'Koffi Marc', matricule: 'ELV-2026-0420' },
]

export const RECU = { numero: 'REC-000241', montant: 145000 }

export const INDICATEURS = {
  presents: { presents: 32, effectif: EFFECTIF, variation: 2 },
  notesSaisies: { valeur: 48, variation: -6 },
  inscrits: { valeur: EFFECTIF },
  resteAPayer: { montant: 310000 },
}

export const ABSENCES = [
  { id: 'a1', initiales: 'YS', nom: 'Yao Serge Emmanuel', etat: 'NON_JUSTIFIE' as CodeEtat },
  { id: 'a2', initiales: 'DF', nom: 'Diabaté Fatoumata', etat: 'JUSTIFIE' as CodeEtat },
  { id: 'a3', initiales: 'BO', nom: 'Bamba Ousmane', retardMinutes: 12 },
]

export const NOTE_DICTEE = { valeur: '14.25', bareme: '20' }
export const MONTANT_VERSE = 145000
export const DERNIER_ENREGISTREMENT = '2026-08-18T10:42:00'

/** Les blocs du tableau composé : ce que le serveur dira pour chaque domaine, ici figé. */
export const BLOCS: Record<
  string,
  { nombre?: number; montant?: number; valeurCle?: string; cle: string; parametres?: Record<string, string | number>; reservee?: boolean }
> = {
  scolarite: { nombre: 12, cle: 'accueil.bloc.scolarite' },
  vie_scolaire: { nombre: 4, cle: 'accueil.bloc.vie_scolaire' },
  pedagogie: { nombre: 3, cle: 'accueil.bloc.pedagogie' },
  evaluation: { nombre: 27, cle: 'accueil.bloc.evaluation' },
  conseil: { valeurCle: 'accueil.bloc.conseil_valeur', cle: 'accueil.bloc.conseil', parametres: { classe: CLASSE } },
  finance: { montant: 8150000, cle: 'accueil.bloc.finance', parametres: { n: 61 }, reservee: true },
  personnel: { nombre: 2, cle: 'accueil.bloc.personnel' },
  communication: { nombre: 18, cle: 'accueil.bloc.communication' },
  tenant: { nombre: 5, cle: 'accueil.bloc.tenant' },
}
