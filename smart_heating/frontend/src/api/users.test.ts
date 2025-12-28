import { describe, it, expect, vi, beforeEach } from 'vitest'
import { apiClient } from './client'
import * as api from './users'

vi.mock('./client')
const mockedClient = vi.mocked(apiClient)

describe('API - Users', () => {
  beforeEach(() => vi.clearAllMocks())

  it('user management endpoints', async () => {
    mockedClient.get.mockResolvedValue({ data: { users: [] } } as any)
    const users = await api.getUsers()
    expect(users).toBeDefined()

    mockedClient.get.mockResolvedValue({ data: { user: { user_id: 'u1' } } } as any)
    const user = await api.getUser('u1')
    expect(user.user.user_id).toBe('u1')

    mockedClient.post.mockResolvedValue({ data: { user: { user_id: 'u2' } } } as any)
    const created = await api.createUser({ user_id: 'u2', name: 'U2', person_entity: 'p2' } as any)
    expect(created.user.user_id).toBe('u2')

    mockedClient.post.mockResolvedValue({ data: { user: { user_id: 'u2', name: 'New' } } } as any)
    const updated = await api.updateUser('u2', { name: 'New' })
    expect(updated.user.name).toBe('New')

    mockedClient.delete.mockResolvedValue({ data: { message: 'ok' } } as any)
    const del = await api.deleteUser('u2')
    expect(del.message).toBe('ok')

    mockedClient.post.mockResolvedValue({ data: { settings: { enabled: true } } } as any)
    const set = await api.updateUserSettings({ enabled: true } as any)
    expect(set.settings.enabled).toBe(true)
  })
})
