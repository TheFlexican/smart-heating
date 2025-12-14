import axios from 'axios'
const API_BASE = '/api/smart_heating'

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
  const response = await axios.get(`${API_BASE}/safety_sensor`)
  return response.data
}

export const setSafetySensor = async (config: {
  sensor_id: string
  attribute?: string
  alert_value?: string | boolean
  enabled?: boolean
}): Promise<void> => {
  await axios.post(`${API_BASE}/safety_sensor`, config)
}

export const removeSafetySensor = async (sensorId: string): Promise<void> => {
  await axios.delete(`${API_BASE}/safety_sensor?sensor_id=${encodeURIComponent(sensorId)}`)
}

export default {}
