import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import * as api from './users'

vi.mock('axios')
const mockedAxios = axios as unknown as jest.Mocked<typeof axios>

describe('API - Users', () => {
  beforeEach(() => vi.clearAllMocks())

  it('user management endpoints', async () => {
    mockedAxios.get = vi.fn().mockResolvedValue({ data: { users: [] } }) as any
    const users = await api.getUsers()
    expect(users).toBeDefined()

    mockedAxios.get = vi.fn().mockResolvedValue({ data: { user: { user_id: 'u1' } } }) as any
    const user = await api.getUser('u1')
    expect(user.user.user_id).toBe('u1')

    mockedAxios.post = vi.fn().mockResolvedValue({ data: { user: { user_id: 'u2' } } }) as any
    const created = await api.createUser({ user_id: 'u2', name: 'U2', person_entity: 'p2' } as any)
    expect(created.user.user_id).toBe('u2')

    mockedAxios.post = vi
      .fn()
      .mockResolvedValue({ data: { user: { user_id: 'u2', name: 'New' } } }) as any
    const updated = await api.updateUser('u2', { name: 'New' })
    expect(updated.user.name).toBe('New')

    mockedAxios.delete = vi.fn().mockResolvedValue({ data: { message: 'ok' } }) as any
    const del = await api.deleteUser('u2')
    expect(del.message).toBe('ok')

    mockedAxios.post = vi.fn().mockResolvedValue({ data: { settings: { enabled: true } } }) as any
    const set = await api.updateUserSettings({ enabled: true } as any)
    expect(set.settings.enabled).toBe(true)
  })
})
