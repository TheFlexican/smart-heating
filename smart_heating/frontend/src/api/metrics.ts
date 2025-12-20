import axios from 'axios'
const API_BASE = '/api/smart_heating'

export const getAdvancedMetrics = async (minutesOrDays: number, areaId?: string): Promise<any> => {
  // Prefer minutes-based queries from the UI; backend supports `minutes`.
  const params = new URLSearchParams()
  // If the value is one of the minute options (1,2,3,5) send as minutes
  if ([1, 2, 3, 5].includes(minutesOrDays)) {
    params.append('minutes', minutesOrDays.toString())
  } else {
    params.append('days', minutesOrDays.toString())
  }
  if (areaId) {
    params.append('area_id', areaId)
  }
  const response = await axios.get(`${API_BASE}/metrics/advanced?${params.toString()}`)
  return response.data
}

export default {}
