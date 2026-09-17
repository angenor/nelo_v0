// US3 : chaque persona est un ContexteCapacites valide contre le schéma du contrat, sans rôle.
import { readdirSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import pack from '../../app/core/demonstration/pack-demonstration.json'

type Schema = Record<string, any>
const racine = resolve(import.meta.dirname, '../../..')
const contrat = JSON.parse(readFileSync(resolve(racine, 'contrat/openapi.json'), 'utf8'))
const dossier = resolve(racine, 'web/app/core/demonstration/personas')
const personas = readdirSync(dossier).filter((f) => f.endsWith('.json'))

const FORMATS: Record<string, RegExp> = {
  uuid: /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i,
  date: /^\d{4}-\d{2}-\d{2}$/,
}

/** Un validateur JSON Schema minimal : ce que Pydantic produit pour ContexteCapacites, et rien d'autre. */
function valider(schema: Schema, valeur: unknown, chemin: string, erreurs: string[]): void {
  if (schema.$ref) {
    const nom = String(schema.$ref).split('/').pop()!
    return valider(contrat.components.schemas[nom], valeur, chemin, erreurs)
  }
  if (schema.anyOf) {
    const essais = schema.anyOf.map((s: Schema) => {
      const e: string[] = []
      valider(s, valeur, chemin, e)
      return e
    })
    if (!essais.some((e: string[]) => e.length === 0)) erreurs.push(`${chemin} : aucune branche de anyOf`)
    return
  }
  const type = schema.type
  const genre = valeur === null ? 'null' : Array.isArray(valeur) ? 'array' : typeof valeur
  if (type === 'integer' && !Number.isInteger(valeur)) erreurs.push(`${chemin} : entier attendu`)
  else if (type === 'number' && genre !== 'number') erreurs.push(`${chemin} : nombre attendu`)
  else if (type && !['integer', 'number'].includes(type) && type !== genre) {
    erreurs.push(`${chemin} : ${type} attendu, ${genre} reçu`)
    return
  }
  if (schema.enum && !schema.enum.includes(valeur)) erreurs.push(`${chemin} : hors énumération`)
  if (schema.const !== undefined && schema.const !== valeur) erreurs.push(`${chemin} : constante attendue`)
  if (typeof valeur === 'string') {
    if (schema.pattern && !new RegExp(schema.pattern).test(valeur)) erreurs.push(`${chemin} : motif ${schema.pattern}`)
    if (schema.minLength && valeur.length < schema.minLength) erreurs.push(`${chemin} : trop court`)
    if (schema.format && FORMATS[schema.format] && !FORMATS[schema.format]!.test(valeur)) {
      erreurs.push(`${chemin} : format ${schema.format}`)
    }
  }
  if (typeof valeur === 'number') {
    if (schema.minimum !== undefined && valeur < schema.minimum) erreurs.push(`${chemin} : sous le minimum`)
    if (schema.maximum !== undefined && valeur > schema.maximum) erreurs.push(`${chemin} : au-dessus du maximum`)
  }
  if (Array.isArray(valeur)) {
    if (schema.minItems && valeur.length < schema.minItems) erreurs.push(`${chemin} : trop peu d’éléments`)
    valeur.forEach((v, i) => schema.items && valider(schema.items, v, `${chemin}[${i}]`, erreurs))
  }
  if (genre === 'object') {
    const objet = valeur as Record<string, unknown>
    for (const requis of schema.required ?? []) {
      if (!(requis in objet)) erreurs.push(`${chemin}.${requis} : requis`)
    }
    for (const [cle, v] of Object.entries(objet)) {
      const propre = schema.properties?.[cle]
      if (propre) valider(propre, v, `${chemin}.${cle}`, erreurs)
      else if (schema.additionalProperties === false) erreurs.push(`${chemin}.${cle} : propriété interdite`)
      else if (typeof schema.additionalProperties === 'object') {
        valider(schema.additionalProperties, v, `${chemin}.${cle}`, erreurs)
      }
    }
  }
}

function cles(valeur: unknown): string[] {
  if (Array.isArray(valeur)) return valeur.flatMap(cles)
  if (valeur && typeof valeur === 'object') {
    return Object.entries(valeur).flatMap(([k, v]) => [k, ...cles(v)])
  }
  return []
}

describe('le validateur minimal', () => {
  it('refuse une propriété en trop et un code de capacité malformé', () => {
    const persona = JSON.parse(readFileSync(resolve(dossier, 'sept-domaines.json'), 'utf8'))
    const erreurs: string[] = []
    valider({ $ref: '#/components/schemas/ContexteCapacites' }, { ...persona, role: 'X' }, '$', erreurs)
    persona.capacites[0].code = 'finance'
    valider({ $ref: '#/components/schemas/ContexteCapacites' }, persona, '$', erreurs)
    expect(erreurs.join('\n')).toMatch(/role : propriété interdite/)
    expect(erreurs.join('\n')).toMatch(/code : motif/)
  })
})

describe.each(personas)('%s', (fichier) => {
  const persona = JSON.parse(readFileSync(resolve(dossier, fichier), 'utf8'))

  it('est un ContexteCapacites valide contre contrat/openapi.json', () => {
    const erreurs: string[] = []
    valider({ $ref: '#/components/schemas/ContexteCapacites' }, persona, '$', erreurs)
    expect(erreurs).toEqual([])
  })

  it('ne porte aucune clé « role » et emploie le pack de démonstration', () => {
    expect(cles(persona).filter((k) => /role/i.test(k))).toEqual([])
    expect(persona.country_pack).toEqual(pack)
  })

  it('nomme l’administrateur de son établissement', () => {
    const actif = persona.etablissements.find((e: { id: string }) => e.id === persona.etablissement_actif)
    expect(actif.administrateur.telephone).not.toBe('')
  })
})

it('les quatre personas existent', () => {
  expect(personas.sort()).toEqual([
    'aucune-capacite.json',
    'cinq-domaines.json',
    'sept-domaines.json',
    'un-domaine.json',
  ])
})
