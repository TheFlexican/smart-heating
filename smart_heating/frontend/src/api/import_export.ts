import { apiClient } from './client'

export const exportConfig = async (): Promise<Blob> => {
  const response = await apiClient.get('/export', {
    responseType: 'blob',
  })
  return response.data
}

export const importConfig = async (configData: any): Promise<any> => {
  const response = await apiClient.post('/import', configData)
  return response.data
}

export const validateConfig = async (configData: any): Promise<any> => {
  const response = await apiClient.post('/validate', configData)
  return response.data
}

export const listBackups = async (): Promise<any> => {
  const response = await apiClient.get('/backups')
  return response.data
}

export const restoreBackup = async (filename: string): Promise<any> => {
  const response = await apiClient.post(`/backups/${filename}/restore`)
  return response.data
}

export default {}
