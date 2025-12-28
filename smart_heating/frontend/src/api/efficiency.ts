import { apiClient } from './client'

type Period = 'day' | 'week' | 'month' | 'year'

export const getEfficiencyReport = async (
  areaId: string,
  period: Period = 'week',
): Promise<any> => {
  const response = await apiClient.get(`/efficiency/report/${areaId}?period=${period}`)
  return response.data
}

export const getAllAreasEfficiency = async (period: Period = 'week'): Promise<any> => {
  const response = await apiClient.get(`/efficiency/all_areas?period=${period}`)
  return response.data
}

export const getEfficiencyHistory = async (areaId: string, days: number = 30): Promise<any> => {
  const response = await apiClient.get(`/efficiency/history/${areaId}?days=${days}`)
  return response.data
}

export const getComparison = async (period: Period): Promise<any> => {
  const response = await apiClient.get(`/comparison/${period}`)
  return response.data
}

export const getCustomComparison = async (
  startA: string,
  endA: string,
  startB: string,
  endB: string,
): Promise<any> => {
  const response = await apiClient.post('/comparison/custom', {
    start_a: startA,
    end_a: endA,
    start_b: startB,
    end_b: endB,
  })
  return response.data
}

export default {}
