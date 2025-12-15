import axios from 'axios'
const API_BASE = '/api/smart_heating'

export const exportConfig = async (): Promise<Blob> => {
  const response = await axios.get(`${API_BASE}/export`, {
    responseType: 'blob',
  })
  return response.data
}

export const importConfig = async (configData: any): Promise<any> => {
  const response = await axios.post(`${API_BASE}/import`, configData)
  return response.data
}

export const validateConfig = async (configData: any): Promise<any> => {
  const response = await axios.post(`${API_BASE}/validate`, configData)
  return response.data
}

export const listBackups = async (): Promise<any> => {
  const response = await axios.get(`${API_BASE}/backups`)
  return response.data
}

export const restoreBackup = async (filename: string): Promise<any> => {
  const response = await axios.post(`${API_BASE}/backups/${filename}/restore`)
  return response.data
}

export default {}
