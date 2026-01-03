import { apiClient } from './client'

export const getAdvancedMetrics = async (
  value: number,
  areaId?: string,
  forceDays?: boolean,
  forceHours?: boolean,
): Promise<any> => {
  const params = new URLSearchParams()

  // Determine which parameter to use based on flags
  if (forceHours) {
    params.append('hours', value.toString())
  } else if (forceDays) {
    params.append('days', value.toString())
  } else if ([1, 2, 3, 5].includes(value)) {
    // Backward compatibility: treat as minutes if no force flags
    params.append('minutes', value.toString())
  } else {
    params.append('days', value.toString())
  }

  if (areaId) {
    params.append('area_id', areaId)
  }

  const response = await apiClient.get(`/metrics/advanced?${params.toString()}`)
  return response.data
}

export default {}
