import axios from 'axios'
import { Area, ScheduleEntry, LearningStats, DeviceAdd } from '../types'

type PresetConfig = Record<string, boolean | number | string | null>
type PresetResponse = Record<string, boolean | number | string | null>
type BoostPayload = { duration: number; temperature?: number }
type CopySchedulePayload = {
  source_area_id: string
  target_area_id: string
  source_days?: string[]
  target_days?: string[]
}

const API_BASE = '/api/smart_heating'

export const getZones = async (): Promise<Area[]> => {
  const response = await axios.get(`${API_BASE}/areas`)
  return response.data.areas
}

export const getZone = async (areaId: string): Promise<Area> => {
  const response = await axios.get(`${API_BASE}/areas/${areaId}`)
  return response.data
}

export const addDeviceToZone = async (areaId: string, device: DeviceAdd): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/devices`, device)
}

export const removeDeviceFromZone = async (areaId: string, deviceId: string): Promise<void> => {
  await axios.delete(`${API_BASE}/areas/${areaId}/devices/${deviceId}`)
}

export const setZoneTemperature = async (areaId: string, temperature: number): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/temperature`, { temperature })
}

export const setZoneHvacMode = async (areaId: string, hvacMode: string): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/hvac_mode`, { hvac_mode: hvacMode })
}

export const enableZone = async (areaId: string): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/enable`)
}

export const disableZone = async (areaId: string): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/disable`)
}

export const hideZone = async (areaId: string): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/hide`)
}

export const unhideZone = async (areaId: string): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/unhide`)
}

export const addScheduleToZone = async (
  areaId: string,
  schedule: Omit<ScheduleEntry, 'id'>,
): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/schedules`, schedule)
}

export const removeScheduleFromZone = async (areaId: string, scheduleId: string): Promise<void> => {
  await axios.delete(`${API_BASE}/areas/${areaId}/schedules/${scheduleId}`)
}

export const updateScheduleInZone = async (
  areaId: string,
  scheduleId: string,
  update: Partial<Omit<ScheduleEntry, 'id'>>,
): Promise<void> => {
  await axios.patch(`${API_BASE}/areas/${areaId}/schedules/${scheduleId}`, update)
}

export const getLearningStats = async (areaId: string): Promise<LearningStats> => {
  const response = await axios.get(`${API_BASE}/areas/${areaId}/learning`)
  return response.data.stats
}

// Preset Modes
export const setPresetMode = async (areaId: string, presetMode: string): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/preset_mode`, { preset_mode: presetMode })
}

// Boost Mode
export const setBoostMode = async (
  areaId: string,
  duration: number,
  temperature?: number,
): Promise<void> => {
  const data: BoostPayload = { duration }
  if (temperature !== undefined) {
    data.temperature = temperature
  }
  await axios.post(`${API_BASE}/areas/${areaId}/boost`, data)
}

export const cancelBoost = async (areaId: string): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/cancel_boost`)
}

export const setHvacMode = async (areaId: string, hvacMode: string): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/hvac_mode`, {
    hvac_mode: hvacMode,
  })
}

export const setSwitchShutdown = async (areaId: string, shutdown: boolean): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/switch_shutdown`, {
    shutdown,
  })
}

export const copySchedule = async (
  sourceAreaId: string,
  targetAreaId: string,
  sourceDays?: string[],
  targetDays?: string[],
): Promise<void> => {
  const data: CopySchedulePayload = {
    source_area_id: sourceAreaId,
    target_area_id: targetAreaId,
  }
  if (sourceDays) {
    data.source_days = sourceDays
  }
  if (targetDays) {
    data.target_days = targetDays
  }
  await axios.post(`${API_BASE}/copy_schedule`, data)
}

export const setHeatingType = async (
  areaId: string,
  heatingType: 'radiator' | 'floor_heating' | 'airco',
  customOverheadTemp?: number,
): Promise<void> => {
  const data: any = { heating_type: heatingType }
  if (customOverheadTemp !== undefined) {
    data.custom_overhead_temp = customOverheadTemp
  }
  await axios.post(`${API_BASE}/areas/${areaId}/heating_type`, data)
}

export const setAreaPresetConfig = async (
  areaId: string,
  config: Partial<PresetConfig>,
): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/preset_config`, config)
}

export const getAreaPresetConfig = async (areaId: string): Promise<PresetResponse> => {
  const response = await axios.get(`${API_BASE}/areas/${areaId}/preset_config`)
  return response.data
}

export const setAreaHeatingCurve = async (
  areaId: string,
  useGlobal: boolean,
  coefficient?: number,
): Promise<void> => {
  const data: { use_global: boolean; coefficient?: number } = { use_global: useGlobal }
  if (coefficient !== undefined) {
    data.coefficient = coefficient
  }
  await axios.post(`${API_BASE}/areas/${areaId}/heating_curve`, data)
}

export const setManualOverride = async (areaId: string, enabled: boolean): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/manual_override`, { enabled })
}

export const setPrimaryTemperatureSensor = async (
  areaId: string,
  sensorId: string | null,
): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/primary_temp_sensor`, { sensor_id: sensorId })
}

export default {}
