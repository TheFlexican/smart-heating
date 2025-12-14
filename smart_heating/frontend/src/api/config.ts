import axios from 'axios'
const API_BASE = '/api/smart_heating'

export const getStatus = async (): Promise<any> => {
  const response = await axios.get(`${API_BASE}/status`)
  return response.data
}

export const getConfig = async (): Promise<any> => {
  const response = await axios.get(`${API_BASE}/config`)
  return response.data
}

export const getAdvancedControlConfig = async (): Promise<any> => {
  const response = await axios.get(`${API_BASE}/config/advanced_control`)
  return response.data
}

export const setAdvancedControlConfig = async (config: any): Promise<void> => {
  await axios.post(`${API_BASE}/config/advanced_control`, config)
}

export const setFrostProtection = async (
  enabled: boolean,
  temperature: number
): Promise<void> => {
  await axios.post(`${API_BASE}/frost_protection`, {
    enabled,
    temperature
  })
}

export const getEntityState = async (entityId: string): Promise<any> => {
  const response = await axios.get(`${API_BASE}/entity_state/${entityId}`)
  return response.data
}

export const getBinarySensorEntities = async (): Promise<any[]> => {
  const response = await axios.get(`${API_BASE}/entities/binary_sensor`)
  return response.data.entities
}

export const getWeatherEntities = async (): Promise<any[]> => {
  const response = await axios.get(`${API_BASE}/entities/weather`)
  return response.data.entities
}

export default {}
