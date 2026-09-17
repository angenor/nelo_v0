// Le type du contexte vient du contrat, jamais d'une réécriture locale (CP-05, research.md R-05).
import type { components } from '../../../../contrat/client'

type Schemas = components['schemas']

export type ContexteCapacites = Schemas['ContexteCapacites']
export type Compte = Schemas['Compte']
export type EtablissementContexte = Schemas['EtablissementContexte']
export type Administrateur = Schemas['Administrateur']
export type AnneeContexte = Schemas['AnneeContexte']
export type CapaciteContexte = Schemas['CapaciteContexte']
export type AccesNominatif = Schemas['AccesNominatif']
export type CountryPackContexte = Schemas['CountryPackContexte']
export type Devise = Schemas['Devise']
export type AlerteContexte = Schemas['AlerteContexte']
