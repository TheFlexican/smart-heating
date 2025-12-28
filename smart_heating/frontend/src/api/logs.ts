import { apiClient } from './client'

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
  },
): Promise<AreaLogEntry[]> => {
  const params = new URLSearchParams()
  if (options?.limit) {
    params.append('limit', options.limit.toString())
  }
  if (options?.type) {
    params.append('type', options.type)
  }

  const response = await apiClient.get(`/areas/${areaId}/logs?${params.toString()}`)
  return response.data.logs
}

export const getHysteresis = async (): Promise<number> => {
  const response = await apiClient.get('/hysteresis')
  return response.data.hysteresis
}

export const setHysteresis = async (hysteresis: number): Promise<void> => {
  await apiClient.post('/hysteresis', { hysteresis })
}

export default {}
