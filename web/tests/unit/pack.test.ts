import { describe, expect, it } from 'vitest'
import demonstration from '../../app/core/demonstration/pack-demonstration.json'
import fictif from '../../app/core/demonstration/pack-fictif.json'
import { creerPack, ESPACE_FINE as F } from '../../app/core/pack/pack'

const CODES_NEUTRES = [
  'ANNEE', 'PERIODE', 'CLASSE', 'PROFESSEUR_PRINCIPAL', 'BULLETIN', 'NOTE', 'MENTION', 'RANG',
  'RESPONSABLE', 'CHEF_ETABLISSEMENT', 'CENSEUR', 'ECONOME', 'INSTANCE_PARENTS', 'FRAIS_SCOLARITE',
  'EXAMEN_NATIONAL', 'CONSEIL_ELEVES', 'CONSEIL_CLASSE',
]

describe('les packs de démonstration', () => {
  it('portent les dix-sept codes neutres, en fr et en en', () => {
    for (const pack of [demonstration, fictif]) {
      expect(Object.keys(pack.vocabulaire).sort()).toEqual([...CODES_NEUTRES].sort())
      for (const libelles of Object.values(pack.vocabulaire)) {
        expect(Object.keys(libelles).sort()).toEqual(['en', 'fr'])
      }
    }
  })
})

describe('montant', () => {
  const fr = creerPack(demonstration, 'fr')

  it('écrit un entier sans exposant avec l’espace fine et le symbole du pack', () => {
    expect(fr.montant(145000)).toBe(`145${F}000${F}F`)
    expect(fr.montant(8150000)).toBe(`8${F}150${F}000${F}F`)
    expect(fr.montant(0)).toBe(`0${F}F`)
    expect(fr.montant(-2500)).toBe(`-2${F}500${F}F`)
    expect(fr.montant(145000, { symbole: false })).toBe(`145${F}000`)
  })

  it('place la virgule selon l’exposant de la devise', () => {
    const p = creerPack(fictif, 'fr')
    expect(p.montant(145000)).toBe(`1${F}450,00${F}¤`)
    expect(p.montant(5)).toBe(`0,05${F}¤`)
    expect(creerPack(fictif, 'en').montant(145000)).toBe(`1,450.00${F}¤`)
  })

  it('refuse ce qui n’est pas un entier sûr', () => {
    expect(fr.montant(12.5)).toBe('')
    expect(fr.montant(Number.MAX_SAFE_INTEGER + 2)).toBe('')
  })
})

describe('note', () => {
  it('écrit la chaîne décimale et son barème, sans rien calculer', () => {
    expect(creerPack(demonstration, 'fr').note('14.25', '20')).toBe(`14,25${F}/${F}20`)
    expect(creerPack(demonstration, 'en').note('14.25', '20')).toBe(`14.25${F}/${F}20`)
    expect(creerPack(demonstration, 'fr').note('14.250', '20')).toBe(`14,250${F}/${F}20`)
    expect(creerPack(demonstration, 'fr').note('abc', '20')).toBe('')
  })
})

describe('libelle', () => {
  it('résout un code selon le pack et la langue', () => {
    expect(creerPack(demonstration, 'fr').libelle('CLASSE')).toBe('Classe')
    expect(creerPack(demonstration, 'en').libelle('CLASSE')).toBe('Class')
    expect(creerPack(fictif, 'fr').libelle('CLASSE')).toBe('Form')
    expect(creerPack(demonstration, 'fr').libelle('INCONNU')).toBe('')
  })

  it('replie une langue absente du pack sur sa première langue', () => {
    const p = creerPack(demonstration, 'de')
    expect(p.langue).toBe('fr')
    expect(p.libelle('CLASSE')).toBe('Classe')
  })
})

describe('date', () => {
  it('écrit un jour scolaire avec une majuscule initiale', () => {
    expect(creerPack(demonstration, 'fr').date('2026-08-18')).toBe('Mardi 18 août')
    expect(creerPack(demonstration, 'en').date('2026-08-18')).toMatch(/^Tuesday/)
    expect(creerPack(demonstration, 'fr').date('pas-une-date')).toBe('')
    expect(creerPack(demonstration, 'fr').jourMois('2026-08-12')).toBe('12 août')
  })
})
