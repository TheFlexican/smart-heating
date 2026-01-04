import { describe, it, expect, vi, beforeEach } from 'vitest'
import { apiClient } from './client'
import * as api from './devices'

vi.mock('./client')
const mockedClient = vi.mocked(apiClient)

describe('API - Devices', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getDevices and refreshDevices', async () => {
    mockedClient.get.mockResolvedValue({ data: { devices: [{ id: 'd1' }] } } as any)
    const devices = await api.getDevices()
    expect(devices).toEqual([{ id: 'd1' }])

    mockedClient.get.mockResolvedValue({
      data: { success: true, updated: 1, available: 2, message: 'ok' },
    } as any)
    const refresh = await api.refreshDevices()
    expect(refresh.success).toBe(true)
    expect(mockedClient.get).toHaveBeenCalledWith('/devices/refresh')
  })
})
