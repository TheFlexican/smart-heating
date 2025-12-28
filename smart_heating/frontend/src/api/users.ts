import { apiClient } from './client'
import { UserProfile, UserData, MultiUserSettings, PresenceState } from '../types'

export const getUsers = async (): Promise<UserData> => {
  const response = await apiClient.get('/users')
  return response.data
}

export const getUser = async (userId: string): Promise<{ user: UserProfile }> => {
  const response = await apiClient.get(`/users/${userId}`)
  return response.data
}

export const createUser = async (user: any): Promise<{ user: UserProfile }> => {
  const response = await apiClient.post('/users', user)
  return response.data
}

export const updateUser = async (
  userId: string,
  updates: Partial<any>,
): Promise<{ user: UserProfile }> => {
  const response = await apiClient.post(`/users/${userId}`, updates)
  return response.data
}

export const deleteUser = async (userId: string): Promise<{ message: string }> => {
  const response = await apiClient.delete(`/users/${userId}`)
  return response.data
}

export const updateUserSettings = async (
  settings: Partial<MultiUserSettings>,
): Promise<{ settings: MultiUserSettings }> => {
  const response = await apiClient.post('/users/settings', settings)
  return response.data
}

export const getPresenceState = async (): Promise<{ presence_state: PresenceState }> => {
  const response = await apiClient.get('/users/presence')
  return response.data
}

export const getActivePreferences = async (areaId?: string): Promise<any> => {
  const url = areaId
    ? `/users/preferences?area_id=${encodeURIComponent(areaId)}`
    : '/users/preferences'
  const response = await apiClient.get(url)
  return response.data
}

export default {}
