import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import * as api from './devices'

vi.mock('axios')
const mockedAxios = axios as unknown as jest.Mocked<typeof axios>

describe('API - Devices', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getDevices and refreshDevices', async () => {
    mockedAxios.get = vi.fn().mockResolvedValue({ data: { devices: [{ id: 'd1' }]} }) as any
    const devices = await api.getDevices()
    expect(devices).toEqual([{ id: 'd1' }])

    mockedAxios.get = vi.fn().mockResolvedValue({ data: { success: true, updated: 1, available: 2, message: 'ok' }}) as any
    const refresh = await api.refreshDevices()
    expect(refresh.success).toBe(true)
    expect(mockedAxios.get).toHaveBeenCalledWith('/api/smart_heating/devices/refresh')
  })

  it('setHideDevicesPanel toggles the flag', async () => {
    mockedAxios.post = vi.fn().mockResolvedValue({ data: {} }) as any
    await api.setHideDevicesPanel(true)
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/smart_heating/hide_devices_panel', { hide_devices_panel: true })
  })
})
