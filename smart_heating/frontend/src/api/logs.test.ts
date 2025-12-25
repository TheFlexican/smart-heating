import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import * as logs from './logs'

vi.mock('axios')
const mockedAxios = axios as unknown as jest.Mocked<typeof axios>

describe('API - Logs', () => {
  beforeEach(() => vi.clearAllMocks())

  it('set and get hysteresis endpoint', async () => {
    mockedAxios.post = vi.fn().mockResolvedValue({ data: {} }) as any
    await logs.setHysteresis(0.5)
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/smart_heating/hysteresis', {
      hysteresis: 0.5,
    })

    mockedAxios.get = vi.fn().mockResolvedValue({ data: { hysteresis: 0.7 } }) as any
    const h = await logs.getHysteresis()
    expect(h).toBe(0.7)
  })

  it('get area logs with params', async () => {
    mockedAxios.get = vi.fn().mockResolvedValue({ data: { logs: [] } }) as any
    await logs.getAreaLogs('a1')
    expect(mockedAxios.get).toHaveBeenCalledWith('/api/smart_heating/areas/a1/logs?')
    await logs.getAreaLogs('a1', { limit: 5, type: 'warning' })
    expect(mockedAxios.get).toHaveBeenCalledWith(
      '/api/smart_heating/areas/a1/logs?limit=5&type=warning',
    )
  })
})
