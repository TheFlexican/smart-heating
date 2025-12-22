import { Zone, GlobalPresets } from '../../../types'

export const isEnabledVal = (v: boolean | string | undefined | null) =>
  v === true || String(v) === 'true'

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
    const val = (globalPresets as any)[globalKey]
    return `${val ?? fallback}°C (global)`
  }

  return `${customTemp ?? fallback}°C (custom)`
}

export default { isEnabledVal, getPresetTemp }
