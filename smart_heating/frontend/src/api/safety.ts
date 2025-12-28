import { apiClient } from './client'

export interface SafetySensor {
  sensor_id: string
  attribute: string
  alert_value: string | boolean
  enabled: boolean
}

export interface SafetySensorResponse {
  sensors: SafetySensor[]
  alert_active?: boolean
}

export const getSafetySensor = async (): Promise<SafetySensorResponse> => {
  const response = await apiClient.get('/safety_sensor')
  return response.data
}

export const setSafetySensor = async (config: {
  sensor_id: string
  attribute?: string
  alert_value?: string | boolean
  enabled?: boolean
}): Promise<void> => {
  await apiClient.post('/safety_sensor', config)
}

export const removeSafetySensor = async (sensorId: string): Promise<void> => {
  await apiClient.delete(`/safety_sensor?sensor_id=${encodeURIComponent(sensorId)}`)
}

export default {}
