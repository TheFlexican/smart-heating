import { apiClient } from './client'
import { Area, ScheduleEntry, LearningStats, DeviceAdd } from '../types'

export const getZones = async (): Promise<Area[]> => {
  const response = await apiClient.get('/areas')
  return response.data.areas
}

export const getZone = async (areaId: string): Promise<Area> => {
  const response = await apiClient.get(`/areas/${areaId}`)
  return response.data
}

export const addDeviceToZone = async (areaId: string, device: DeviceAdd): Promise<void> => {
  await apiClient.post(`/areas/${areaId}/devices`, device)
}

export const removeDeviceFromZone = async (areaId: string, deviceId: string): Promise<void> => {
  await apiClient.delete(`/areas/${areaId}/devices/${deviceId}`)
}

export const setZoneTemperature = async (areaId: string, temperature: number): Promise<void> => {
  await apiClient.post(`/areas/${areaId}/temperature`, { temperature })
}

export const setZoneHvacMode = async (areaId: string, hvacMode: string): Promise<void> => {
  await apiClient.post(`/areas/${areaId}/hvac_mode`, { hvac_mode: hvacMode })
}

export const enableZone = async (areaId: string): Promise<void> => {
  await apiClient.post(`/areas/${areaId}/enable`)
}

export const disableZone = async (areaId: string): Promise<void> => {
  await apiClient.post(`/areas/${areaId}/disable`)
}

export const hideZone = async (areaId: string): Promise<void> => {
  await apiClient.post(`/areas/${areaId}/hide`)
}

export const unhideZone = async (areaId: string): Promise<void> => {
  await apiClient.post(`/areas/${areaId}/unhide`)
}

export const addScheduleToZone = async (
  areaId: string,
  schedule: Omit<ScheduleEntry, 'id'>,
): Promise<void> => {
  await apiClient.post(`/areas/${areaId}/schedules`, schedule)
}

export const removeScheduleFromZone = async (areaId: string, scheduleId: string): Promise<void> => {
  await apiClient.delete(`/areas/${areaId}/schedules/${scheduleId}`)
}

export const updateScheduleInZone = async (
  areaId: string,
  scheduleId: string,
  update: Partial<Omit<ScheduleEntry, 'id'>>,
): Promise<void> => {
  await apiClient.patch(`/areas/${areaId}/schedules/${scheduleId}`, update)
}

export const getLearningStats = async (areaId: string): Promise<LearningStats> => {
  const response = await apiClient.get(`/areas/${areaId}/learning`)
  return response.data.stats
}

// Preset Modes
export const setPresetMode = async (areaId: string, presetMode: string): Promise<void> => {
  await apiClient.post(`/areas/${areaId}/preset_mode`, { preset_mode: presetMode })
}

// Boost Mode
export const setBoostMode = async (
  areaId: string,
  duration: number,
  temperature?: number,
): Promise<void> => {
  const data: any = { duration }
  if (temperature !== undefined) {
    data.temperature = temperature
  }
  await apiClient.post(`/areas/${areaId}/boost`, data)
}

export const cancelBoost = async (areaId: string): Promise<void> => {
  await apiClient.post(`/areas/${areaId}/cancel_boost`)
}

export const setHvacMode = async (areaId: string, hvacMode: string): Promise<void> => {
  await apiClient.post(`/areas/${areaId}/hvac_mode`, {
    hvac_mode: hvacMode,
  })
}

export const setSwitchShutdown = async (areaId: string, shutdown: boolean): Promise<void> => {
  await apiClient.post(`/areas/${areaId}/switch_shutdown`, {
    shutdown,
  })
}

export const copySchedule = async (
  sourceAreaId: string,
  targetAreaId: string,
  sourceDays?: string[],
  targetDays?: string[],
): Promise<void> => {
  const data: any = {
    source_area_id: sourceAreaId,
    target_area_id: targetAreaId,
  }
  if (sourceDays) {
    data.source_days = sourceDays
  }
  if (targetDays) {
    data.target_days = targetDays
  }
  await apiClient.post('/copy_schedule', data)
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
  await apiClient.post(`/areas/${areaId}/heating_type`, data)
}

export const setAreaPresetConfig = async (areaId: string, config: Partial<any>): Promise<void> => {
  await apiClient.post(`/areas/${areaId}/preset_config`, config)
}

export const getAreaPresetConfig = async (areaId: string): Promise<any> => {
  const response = await apiClient.get(`/areas/${areaId}/preset_config`)
  return response.data
}

export const setAreaHeatingCurve = async (
  areaId: string,
  useGlobal: boolean,
  coefficient?: number,
): Promise<void> => {
  const data: any = { use_global: useGlobal }
  if (coefficient !== undefined) {
    data.coefficient = coefficient
  }
  await apiClient.post(`/areas/${areaId}/heating_curve`, data)
}

export const setManualOverride = async (areaId: string, enabled: boolean): Promise<void> => {
  await apiClient.post(`/areas/${areaId}/manual_override`, { enabled })
}

export const setPrimaryTemperatureSensor = async (
  areaId: string,
  sensorId: string | null,
): Promise<void> => {
  await apiClient.post(`/areas/${areaId}/primary_temp_sensor`, { sensor_id: sensorId })
}

export const getLearningStatsDetailed = async (areaId: string): Promise<any> => {
  const response = await apiClient.get(`/areas/${areaId}/learning/stats`)
  return response.data.stats
}

export const setAutoPreset = async (
  areaId: string,
  config: {
    auto_preset_enabled?: boolean
    auto_preset_home?: string
    auto_preset_away?: string
  },
): Promise<void> => {
  await apiClient.post(`/areas/${areaId}/auto_preset`, config)
}

export const setAreaHysteresis = async (
  areaId: string,
  config: {
    use_global: boolean
    hysteresis: number | null
  },
): Promise<void> => {
  await apiClient.post(`/areas/${areaId}/hysteresis`, config)
}

export const setNightBoostConfig = async (
  areaId: string,
  config: Record<string, unknown>,
): Promise<void> => {
  await apiClient.post('call_service', {
    service: 'set_night_boost',
    area_id: areaId,
    ...config,
  })
}

export default {}
