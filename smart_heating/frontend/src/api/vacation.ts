import { apiClient } from './client'
import { VacationMode } from '../types'

export const getVacationMode = async (): Promise<VacationMode> => {
  const response = await apiClient.get('/vacation_mode')
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
  const response = await apiClient.post('/vacation_mode', config)
  return response.data
}

export const disableVacationMode = async (): Promise<VacationMode> => {
  const response = await apiClient.delete('/vacation_mode')
  return response.data
}

export default {}
