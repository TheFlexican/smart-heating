import axios from 'axios'
const API_BASE = '/api/smart_heating'

export const getAdvancedMetrics = async (days: 1 | 3 | 7 | 30, areaId?: string): Promise<any> => {
  const params = new URLSearchParams({ days: days.toString() })
  if (areaId) {
    params.append('area_id', areaId)
  }
  const response = await axios.get(`${API_BASE}/metrics/advanced?${params.toString()}`)
  return response.data
}

export default {}
