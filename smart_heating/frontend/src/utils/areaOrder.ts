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

// Helper: Check if parsed data is valid array of strings
function isValidOrderArray(parsed: unknown): parsed is string[] {
  return Array.isArray(parsed) && parsed.every(p => typeof p === 'string')
}

// Helper: Merge zones using saved order
function mergeWithSavedOrder(
  updatedMap: Map<string, Zone>,
  orderIds: string[],
  updatedZones: Zone[],
): Zone[] {
  const ordered: Zone[] = []

  // Add zones in saved order
  for (const id of orderIds) {
    const zone = updatedMap.get(id)
    if (zone) ordered.push(zone)
  }

  // Append new zones not in saved order
  const orderedIds = new Set(orderIds)
  for (const zone of updatedZones) {
    if (!orderedIds.has(zone.id)) ordered.push(zone)
  }

  return ordered
}

// Helper: Try to parse and merge with saved order
function tryMergeWithSavedOrder(
  savedOrderJson: string,
  updatedMap: Map<string, Zone>,
  updatedZones: Zone[],
): Zone[] | null {
  try {
    const parsed = JSON.parse(savedOrderJson)
    if (!isValidOrderArray(parsed)) return null

    return mergeWithSavedOrder(updatedMap, parsed, updatedZones)
  } catch {
    return null
  }
}

// Helper: Merge zones preserving previous order
function mergeWithPreviousOrder(
  prevZones: Zone[],
  updatedMap: Map<string, Zone>,
  updatedZones: Zone[],
): Zone[] {
  const prevIds = new Set(prevZones.map(z => z.id))

  // Map previous zones to updated data
  const merged: Zone[] = prevZones
    .map(p => updatedMap.get(p.id))
    .filter((z): z is Zone => z !== undefined)

  // Append new zones
  for (const zone of updatedZones) {
    if (!prevIds.has(zone.id)) merged.push(zone)
  }

  return merged
}

export function mergeZones(
  prevZones: Zone[],
  updatedZones: Zone[],
  savedOrderJson: string | null,
): Zone[] {
  const updatedMap = new Map(updatedZones.map(z => [z.id, z]))

  // Try saved order first
  if (savedOrderJson) {
    const result = tryMergeWithSavedOrder(savedOrderJson, updatedMap, updatedZones)
    if (result) return result
  }

  // Try previous order
  if (prevZones?.length > 0) {
    return mergeWithPreviousOrder(prevZones, updatedMap, updatedZones)
  }

  // Fallback to updated zones order
  return updatedZones
}

export default mergeZones
