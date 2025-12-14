import axios from 'axios'
const API_BASE = '/api/smart_heating'

export interface AreaLogEntry {
  timestamp: string
  type: string
  message: string
  details: Record<string, any>
}

export const getAreaLogs = async (
  areaId: string,
  options?: {
    limit?: number
    type?: string
  }
): Promise<AreaLogEntry[]> => {
  const params = new URLSearchParams()
  if (options?.limit) {
    params.append('limit', options.limit.toString())
  }
  if (options?.type) {
    params.append('type', options.type)
  }

  const response = await axios.get(`${API_BASE}/areas/${areaId}/logs?${params.toString()}`)
  return response.data.logs
}

export const getHysteresis = async (): Promise<number> => {
  const response = await axios.get(`${API_BASE}/hysteresis`)
  return response.data.hysteresis
}

export const setHysteresis = async (hysteresis: number): Promise<void> => {
  await axios.post(`${API_BASE}/hysteresis`, { hysteresis })
}

export default {}
