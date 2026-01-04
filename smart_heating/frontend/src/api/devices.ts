import { apiClient } from './client'
import { Device } from '../types'

export const getDevices = async (): Promise<Device[]> => {
  const response = await apiClient.get('/devices')
  return response.data.devices
}

export const refreshDevices = async (): Promise<{
  success: boolean
  updated: number
  available: number
  message: string
}> => {
  const response = await apiClient.get('/devices/refresh')
  return response.data
}

export default {}
