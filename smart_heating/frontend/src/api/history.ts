import axios from 'axios'
const API_BASE = '/api/smart_heating'

export const getHistoryConfig = async (): Promise<any> => {
  const response = await axios.get(`${API_BASE}/history/config`)
  return response.data
}

export const setHistoryRetention = async (days: number): Promise<void> => {
  await axios.post(`${API_BASE}/history/config`, {
    retention_days: days
  })
}

export const getHistoryStorageInfo = async (): Promise<any> => {
  const response = await axios.get(`${API_BASE}/history/storage/info`)
  return response.data
}

export const migrateHistoryStorage = async (targetBackend: 'json' | 'database'): Promise<any> => {
  const response = await axios.post(`${API_BASE}/history/storage/migrate`, {
    target_backend: targetBackend
  })
  return response.data
}

export const getDatabaseStats = async (): Promise<any> => {
  const response = await axios.get(`${API_BASE}/history/storage/database/stats`)
  return response.data
}

export const cleanupHistory = async (): Promise<{ success: boolean }> => {
  const response = await axios.post(`${API_BASE}/history/cleanup`)
  return response.data
}

export const getHistory = async (
  areaId: string,
  options?: {
    hours?: number
    startTime?: string
    endTime?: string
  }
): Promise<any> => {
  const params = new URLSearchParams()
  if (options?.hours) {
    params.append('hours', options.hours.toString())
  }
  if (options?.startTime) {
    params.append('start_time', options.startTime)
  }
  if (options?.endTime) {
    params.append('end_time', options.endTime)
  }

  const response = await axios.get(`${API_BASE}/areas/${areaId}/history?${params.toString()}`)
  return response.data
}

export default {}
