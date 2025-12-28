import { apiClient } from './client'

export const getStatus = async (): Promise<any> => {
  const response = await apiClient.get('/status')
  return response.data
}

export const getConfig = async (): Promise<any> => {
  const response = await apiClient.get('/config')
  return response.data
}

export const getAdvancedControlConfig = async (): Promise<any> => {
  const response = await apiClient.get('/config/advanced_control')
  return response.data
}

export const setAdvancedControlConfig = async (config: any): Promise<void> => {
  await apiClient.post('/config/advanced_control', config)
}

export const setFrostProtection = async (enabled: boolean, temperature: number): Promise<void> => {
  await apiClient.post('/frost_protection', {
    enabled,
    temperature,
  })
}

export const getEntityState = async (entityId: string): Promise<any> => {
  const response = await apiClient.get(`/entity_state/${entityId}`)
  return response.data
}

export const getBinarySensorEntities = async (): Promise<any[]> => {
  const response = await apiClient.get('/entities/binary_sensor')
  return response.data.entities
}

export const getWeatherEntities = async (): Promise<any[]> => {
  const response = await apiClient.get('/entities/weather')
  return response.data.entities
}

export const getPersonEntities = async (): Promise<any[]> => {
  // Person entities are included in binary_sensor endpoint with device_class: presence
  const response = await apiClient.get('/entities/binary_sensor')
  return response.data.entities.filter((entity: any) => entity.entity_id.startsWith('person.'))
}

export default {}
