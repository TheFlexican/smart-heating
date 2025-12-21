import axios from 'axios'
import { WindowSensorConfig, PresenceSensorConfig, HassEntity } from '../types'
const API_BASE = '/api/smart_heating'

export const addWindowSensor = async (
  areaId: string,
  config: WindowSensorConfig,
): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/window_sensors`, config)
}

export const removeWindowSensor = async (areaId: string, sensorEntityId: string): Promise<void> => {
  await axios.delete(`${API_BASE}/areas/${areaId}/window_sensors/${sensorEntityId}`)
}

export const addPresenceSensor = async (
  areaId: string,
  config: PresenceSensorConfig,
): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/presence_sensors`, config)
}

export const removePresenceSensor = async (
  areaId: string,
  sensorEntityId: string,
): Promise<void> => {
  await axios.delete(`${API_BASE}/areas/${areaId}/presence_sensors/${sensorEntityId}`)
}

export const getGlobalPresence = async (): Promise<any> => {
  const response = await axios.get(`${API_BASE}/global_presence`)
  return response.data
}

export const setGlobalPresence = async (sensors: PresenceSensorConfig[]): Promise<void> => {
  await axios.post(`${API_BASE}/global_presence`, { sensors })
}

export const setAreaPresenceConfig = async (areaId: string, useGlobal: boolean): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/preset_config`, { use_global_presence: useGlobal })
}

// TRV endpoints
export const getTrvCandidates = async (areaId?: string): Promise<HassEntity[]> => {
  const url = areaId ? `${API_BASE}/areas/${areaId}/trv_candidates` : `${API_BASE}/trv_candidates`
  const response = await axios.get(url)
  // Backend returns { entities: [] }
  return response.data.entities || []
}

export const addTrvEntity = async (
  areaId: string,
  payload: { entity_id: string; role?: 'position' | 'open' | 'both'; name?: string },
): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/trv`, payload)
}

export const removeTrvEntity = async (areaId: string, entityId: string): Promise<void> => {
  await axios.delete(`${API_BASE}/areas/${areaId}/trv/${entityId}`)
}

export default {}
