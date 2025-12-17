import mergeZones from '../areaOrder'

const makeZone = (id: string, name = '') => ({ id, name }) as any

describe('mergeZones', () => {
  it('uses saved order when provided and appends new zones', () => {
    const prev = [makeZone('a'), makeZone('b')]
    const updated = [makeZone('b', 'B'), makeZone('a', 'A'), makeZone('c', 'C')]
    const saved = JSON.stringify(['b', 'a'])

    const result = mergeZones(prev as any, updated as any, saved)

    expect(result.map(z => z.id)).toEqual(['b', 'a', 'c'])
  })

  it('preserves previous client order when no saved order exists', () => {
    const prev = [makeZone('a'), makeZone('b'), makeZone('c')]
    const updated = [makeZone('b', 'B'), makeZone('c', 'C'), makeZone('a', 'A')]

    const result = mergeZones(prev as any, updated as any, null)

    expect(result.map(z => z.id)).toEqual(['a', 'b', 'c'])
    // ensure objects are the updated ones
    expect(result[0].name).toBe('A')
  })

  it('falls back to updatedZones when prev is empty', () => {
    const prev: any[] = []
    const updated = [makeZone('x'), makeZone('y')]

    const result = mergeZones(prev as any, updated as any, null)

    expect(result.map(z => z.id)).toEqual(['x', 'y'])
  })
})
