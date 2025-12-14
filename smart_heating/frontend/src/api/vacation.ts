import axios from 'axios'
import { VacationMode } from '../types'
const API_BASE = '/api/smart_heating'

export const getVacationMode = async (): Promise<VacationMode> => {
  const response = await axios.get(`${API_BASE}/vacation_mode`)
  return response.data
}

export const enableVacationMode = async (config: {
  start_date?: string
  end_date?: string
  preset_mode?: string
  frost_protection_override?: boolean
  min_temperature?: number
  auto_disable?: boolean
  person_entities?: string[]
}): Promise<VacationMode> => {
  const response = await axios.post(`${API_BASE}/vacation_mode`, config)
  return response.data
}

export const disableVacationMode = async (): Promise<VacationMode> => {
  const response = await axios.delete(`${API_BASE}/vacation_mode`)
  return response.data
}

export default {}
