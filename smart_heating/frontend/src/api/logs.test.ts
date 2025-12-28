import { describe, it, expect, vi, beforeEach } from 'vitest'
import { apiClient } from './client'
import * as logs from './logs'

vi.mock('./client')
const mockedClient = vi.mocked(apiClient)

describe('API - Logs', () => {
  beforeEach(() => vi.clearAllMocks())

  it('set and get hysteresis endpoint', async () => {
    mockedClient.post.mockResolvedValue({ data: {} } as any)
    await logs.setHysteresis(0.5)
    expect(mockedClient.post).toHaveBeenCalledWith('/hysteresis', {
      hysteresis: 0.5,
    })

    mockedClient.get.mockResolvedValue({ data: { hysteresis: 0.7 } } as any)
    const h = await logs.getHysteresis()
    expect(h).toBe(0.7)
  })

  it('get area logs with params', async () => {
    mockedClient.get.mockResolvedValue({ data: { logs: [] } } as any)
    await logs.getAreaLogs('a1')
    expect(mockedClient.get).toHaveBeenCalledWith('/areas/a1/logs?')
    await logs.getAreaLogs('a1', { limit: 5, type: 'warning' })
    expect(mockedClient.get).toHaveBeenCalledWith('/areas/a1/logs?limit=5&type=warning')
  })
})
