import { apiClient } from './client'

export const getHistoryConfig = async (): Promise<any> => {
  const response = await apiClient.get('/history/config')
  return response.data
}

export const setHistoryRetention = async (days: number): Promise<void> => {
  await apiClient.post('/history/config', {
    retention_days: days,
  })
}

export const getHistoryStorageInfo = async (): Promise<any> => {
  const response = await apiClient.get('/history/storage/info')
  return response.data
}

export const migrateHistoryStorage = async (targetBackend: 'json' | 'database'): Promise<any> => {
  const response = await apiClient.post('/history/storage/migrate', {
    target_backend: targetBackend,
  })
  return response.data
}

export const getDatabaseStats = async (): Promise<any> => {
  const response = await apiClient.get('/history/storage/database/stats')
  return response.data
}

export const cleanupHistory = async (): Promise<{ success: boolean }> => {
  const response = await apiClient.post('/history/cleanup')
  return response.data
}

export const getHistory = async (
  areaId: string,
  options?: {
    hours?: number
    days?: number
    startTime?: string
    endTime?: string
  },
): Promise<any> => {
  const params = new URLSearchParams()
  if (options?.hours) {
    params.append('hours', options.hours.toString())
  }
  if (options?.days) {
    // Convert days to hours for backend
    params.append('hours', (options.days * 24).toString())
  }
  if (options?.startTime) {
    params.append('start_time', options.startTime)
  }
  if (options?.endTime) {
    params.append('end_time', options.endTime)
  }

  const response = await apiClient.get(`/areas/${areaId}/history?${params.toString()}`)
  return response.data
}

export default {}
