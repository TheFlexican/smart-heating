import axios from 'axios'
const API_BASE = '/api/smart_heating'

type Period = 'day' | 'week' | 'month' | 'year'

export const getEfficiencyReport = async (
  areaId: string,
  period: Period = 'week',
): Promise<any> => {
  const response = await axios.get(`${API_BASE}/efficiency/report/${areaId}?period=${period}`)
  return response.data
}

export const getAllAreasEfficiency = async (period: Period = 'week'): Promise<any> => {
  const response = await axios.get(`${API_BASE}/efficiency/all_areas?period=${period}`)
  return response.data
}

export const getEfficiencyHistory = async (areaId: string, days: number = 30): Promise<any> => {
  const response = await axios.get(`${API_BASE}/efficiency/history/${areaId}?days=${days}`)
  return response.data
}

export const getComparison = async (period: Period): Promise<any> => {
  const response = await axios.get(`${API_BASE}/comparison/${period}`)
  return response.data
}

export const getCustomComparison = async (
  startA: string,
  endA: string,
  startB: string,
  endB: string,
): Promise<any> => {
  const response = await axios.post(`${API_BASE}/comparison/custom`, {
    start_a: startA,
    end_a: endA,
    start_b: startB,
    end_b: endB,
  })
  return response.data
}

export default {}
