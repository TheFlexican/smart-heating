import { Zone, GlobalPresets } from '../types'

/**
 * Accepts boolean or string forms of enabled and returns boolean true only
 */
export const isEnabledVal = (v: boolean | string | undefined | null): boolean => {
  return v === true || String(v) === 'true'
}

/**
 * Compute the display temperature consistently with ZoneCard
 */
export const getDisplayTemperature = (zone: Zone | null | undefined): number => {
  if (!zone) return 20
  const enabled = zone.enabled === true || String(zone.enabled) === 'true'

  // If area is disabled or off, always show base target temperature
  if (!enabled || zone.state === 'off') return zone.target_temperature

  // When not in manual override and an effective target exists, prefer the effective temperature
  if (!zone.manual_override && zone.effective_target_temperature != null) {
    if (Math.abs(zone.effective_target_temperature - zone.target_temperature) >= 0.1) {
      return zone.effective_target_temperature
    }
  }

  // Otherwise show the base target temperature
  return zone.target_temperature
}

/**
 * Get effective preset temperature (global or custom) as a formatted string
 */
export const getPresetTemp = (
  area: Zone | null,
  globalPresets: GlobalPresets | null,
  presetKey: string,
  customTemp: number | undefined,
  fallback: number,
): string => {
  if (!area) return `${fallback}°C`

  const useGlobalKey = `use_global_${presetKey}` as keyof Zone
  const useGlobal = (area[useGlobalKey] as boolean | undefined) ?? true

  if (useGlobal && globalPresets) {
    const globalKey = `${presetKey}_temp` as keyof GlobalPresets
    return `${globalPresets[globalKey]}°C (global)`
  }
  return `${customTemp ?? fallback}°C (custom)`
}
