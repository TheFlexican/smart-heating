import axios from 'axios'
import { Device } from '../types'
const API_BASE = '/api/smart_heating'

export const getDevices = async (): Promise<Device[]> => {
  const response = await axios.get(`${API_BASE}/devices`)
  return response.data.devices
}

export const refreshDevices = async (): Promise<{success: boolean, updated: number, available: number, message: string}> => {
  const response = await axios.get(`${API_BASE}/devices/refresh`)
  return response.data
}

export const setHideDevicesPanel = async (hide: boolean): Promise<void> => {
  await axios.post(`${API_BASE}/hide_devices_panel`, { hide_devices_panel: hide })
}

export default {}
