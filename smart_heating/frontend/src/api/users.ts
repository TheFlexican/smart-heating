import axios from 'axios'
import { UserProfile, UserData, MultiUserSettings, PresenceState } from '../types'
const API_BASE = '/api/smart_heating'

export const getUsers = async (): Promise<UserData> => {
  const response = await axios.get(`${API_BASE}/users`)
  return response.data
}

export const getUser = async (userId: string): Promise<{ user: UserProfile }> => {
  const response = await axios.get(`${API_BASE}/users/${userId}`)
  return response.data
}

export const createUser = async (user: any): Promise<{ user: UserProfile }> => {
  const response = await axios.post(`${API_BASE}/users`, user)
  return response.data
}

export const updateUser = async (
  userId: string,
  updates: Partial<any>,
): Promise<{ user: UserProfile }> => {
  const response = await axios.post(`${API_BASE}/users/${userId}`, updates)
  return response.data
}

export const deleteUser = async (userId: string): Promise<{ message: string }> => {
  const response = await axios.delete(`${API_BASE}/users/${userId}`)
  return response.data
}

export const updateUserSettings = async (
  settings: Partial<MultiUserSettings>,
): Promise<{ settings: MultiUserSettings }> => {
  const response = await axios.post(`${API_BASE}/users/settings`, settings)
  return response.data
}

export const getPresenceState = async (): Promise<{ presence_state: PresenceState }> => {
  const response = await axios.get(`${API_BASE}/users/presence`)
  return response.data
}

export const getActivePreferences = async (areaId?: string): Promise<any> => {
  const url = areaId
    ? `${API_BASE}/users/preferences?area_id=${encodeURIComponent(areaId)}`
    : `${API_BASE}/users/preferences`
  const response = await axios.get(url)
  return response.data
}

export default {}
