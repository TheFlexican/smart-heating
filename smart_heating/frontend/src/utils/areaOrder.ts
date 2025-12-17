import { Zone } from '../types'

/**
 * Merge updated zone list from backend with client-side ordering preference.
 *
 * Behavior:
 * - If savedOrderJson is provided and valid JSON array of ids, follow that order and
 *   append any new zones not present in the saved order.
 * - Otherwise preserve the order of prevZones replacing items with the corresponding
 *   updated zone objects when available, and append any new zones not present in prev.
 * - If prevZones is empty, fall back to updatedZones order.
 */
export function mergeZones(
  prevZones: Zone[],
  updatedZones: Zone[],
  savedOrderJson: string | null,
): Zone[] {
  // Build map of updated zones by id for quick lookup
  const updatedMap = new Map(updatedZones.map(z => [z.id, z]))

  if (savedOrderJson) {
    try {
      const orderIds = JSON.parse(savedOrderJson) as string[]
      const ordered: Zone[] = []
      for (const id of orderIds) {
        const z = updatedMap.get(id)
        if (z) ordered.push(z)
      }
      // Append any zones that are new (not in saved order)
      const orderedIds = new Set(orderIds)
      for (const z of updatedZones) {
        if (!orderedIds.has(z.id)) ordered.push(z)
      }
      return ordered
    } catch {
      // Fallthrough to preserve-prev behavior
    }
  }

  // No saved order -> try to preserve previous client order
  if (prevZones && prevZones.length > 0) {
    const prevIds = new Set(prevZones.map(z => z.id))
    const merged: Zone[] = prevZones
      .map(p => updatedMap.get(p.id) ?? p)
      .filter(z => z !== undefined)
    // Append any new zones that didn't exist before
    for (const z of updatedZones) {
      if (!prevIds.has(z.id)) merged.push(z)
    }
    return merged
  }

  // Fallback: return updated zones as-is
  return updatedZones
}

export default mergeZones
