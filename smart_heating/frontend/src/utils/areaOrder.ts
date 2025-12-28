import { Zone } from '../types'

/**
 * Parse and validate saved order JSON.
 * Returns array of IDs if valid, null otherwise.
 */
function parseSavedOrder(savedOrderJson: string | null): string[] | null {
  if (!savedOrderJson) return null

  try {
    const parsed = JSON.parse(savedOrderJson)
    if (Array.isArray(parsed) && parsed.every(p => typeof p === 'string')) {
      return parsed as string[]
    }
  } catch {
    // Invalid JSON, fall through
  }
  return null
}

/**
 * Apply saved order to zones, appending any new zones not in saved order.
 */
function applyOrderToZones(
  orderIds: string[],
  updatedMap: Map<string, Zone>,
  updatedZones: Zone[],
): Zone[] {
  const ordered: Zone[] = []
  const orderedIds = new Set(orderIds)

  // Add zones in saved order
  for (const id of orderIds) {
    const z = updatedMap.get(id)
    if (z) ordered.push(z)
  }

  // Append new zones not in saved order
  for (const z of updatedZones) {
    if (!orderedIds.has(z.id)) ordered.push(z)
  }

  return ordered
}

/**
 * Preserve previous client order, updating with new zone data.
 */
function preservePreviousOrder(
  prevZones: Zone[],
  updatedMap: Map<string, Zone>,
  updatedZones: Zone[],
): Zone[] {
  const prevIds = new Set(prevZones.map(z => z.id))

  // Keep zones in previous order, but with updated data
  const merged: Zone[] = prevZones
    .map(p => updatedMap.get(p.id))
    .filter((z): z is Zone => z !== undefined)

  // Append any new zones that didn't exist before
  for (const z of updatedZones) {
    if (!prevIds.has(z.id)) merged.push(z)
  }

  return merged
}

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
  const updatedMap = new Map(updatedZones.map(z => [z.id, z]))

  // Try saved order first
  const orderIds = parseSavedOrder(savedOrderJson)
  if (orderIds) {
    return applyOrderToZones(orderIds, updatedMap, updatedZones)
  }

  // Preserve previous client order
  if (prevZones && prevZones.length > 0) {
    return preservePreviousOrder(prevZones, updatedMap, updatedZones)
  }

  // Fallback: return updated zones as-is
  return updatedZones
}

export default mergeZones
