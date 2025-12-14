import axios from 'axios'
const API_BASE = '/api/smart_heating'

export const getGlobalPresets = async (): Promise<any> => {
  const response = await axios.get(`${API_BASE}/global_presets`)
  return response.data
}

export const setGlobalPresets = async (presets: Partial<any>): Promise<void> => {
  await axios.post(`${API_BASE}/global_presets`, presets)
}

export default {}
