import { apiClient } from './client'

export const getGlobalPresets = async (): Promise<any> => {
  const response = await apiClient.get('/global_presets')
  return response.data
}

export const setGlobalPresets = async (presets: Partial<any>): Promise<void> => {
  await apiClient.post('/global_presets', presets)
}

export default {}
