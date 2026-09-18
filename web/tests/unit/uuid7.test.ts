// L'identifiant de requête est un UUID version 7 : sa version et sa variante sont celles de la
// RFC 9562, et deux identifiants tirés à des instants croissants se rangent dans cet ordre.
import { describe, expect, it } from 'vitest'
import { uuid7 } from '../../app/core/api/uuid7'

const FORME = /^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/

describe('uuid7', () => {
  it('a la forme, la version 7 et la variante de la RFC 9562', () => {
    for (let n = 0; n < 200; n++) expect(uuid7()).toMatch(FORME)
  })

  it('porte l’horloge dans ses quarante-huit premiers bits', () => {
    const instant = 1_789_000_000_000
    const identifiant = uuid7(instant)
    const horloge = identifiant.slice(0, 8) + identifiant.slice(9, 13)
    expect(Number.parseInt(horloge, 16)).toBe(instant)
  })

  it('se range dans l’ordre des instants', () => {
    const instants = [1_700_000_000_000, 1_700_000_000_001, 1_800_000_000_000, 1_900_000_000_000]
    const tires = instants.map((instant) => uuid7(instant))
    expect([...tires].sort()).toEqual(tires)
  })

  it('ne se répète pas', () => {
    const tires = new Set(Array.from({ length: 500 }, () => uuid7(1_700_000_000_000)))
    expect(tires.size).toBe(500)
  })
})
