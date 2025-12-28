import { apiClient } from './client'
import { WindowSensorConfig, PresenceSensorConfig, HassEntity } from '../types'

export const addWindowSensor = async (
  areaId: string,
  config: WindowSensorConfig,
): Promise<void> => {
  await apiClient.post(`/areas/${areaId}/window_sensors`, config)
}

export const removeWindowSensor = async (areaId: string, sensorEntityId: string): Promise<void> => {
  await apiClient.delete(`/areas/${areaId}/window_sensors/${sensorEntityId}`)
}

export const addPresenceSensor = async (
  areaId: string,
  config: PresenceSensorConfig,
): Promise<void> => {
  await apiClient.post(`/areas/${areaId}/presence_sensors`, config)
}

export const removePresenceSensor = async (
  areaId: string,
  sensorEntityId: string,
): Promise<void> => {
  await apiClient.delete(`/areas/${areaId}/presence_sensors/${sensorEntityId}`)
}

export const getGlobalPresence = async (): Promise<any> => {
  const response = await apiClient.get('/global_presence')
  return response.data
}

export const setGlobalPresence = async (sensors: PresenceSensorConfig[]): Promise<void> => {
  await apiClient.post('/global_presence', { sensors })
}

export const setAreaPresenceConfig = async (areaId: string, useGlobal: boolean): Promise<void> => {
  await apiClient.post(`/areas/${areaId}/preset_config`, { use_global_presence: useGlobal })
}

// TRV endpoints
export const getTrvCandidates = async (areaId?: string): Promise<HassEntity[]> => {
  const url = areaId ? `/areas/${areaId}/trv_candidates` : '/trv_candidates'
  const response = await apiClient.get(url)
  // Backend returns { entities: [] }
  return response.data.entities || []
}

export const addTrvEntity = async (
  areaId: string,
  payload: { entity_id: string; role?: 'position' | 'open' | 'both'; name?: string },
): Promise<void> => {
  await apiClient.post(`/areas/${areaId}/trv`, payload)
}

export const removeTrvEntity = async (areaId: string, entityId: string): Promise<void> => {
  await apiClient.delete(`/areas/${areaId}/trv/${entityId}`)
}

export default {}
