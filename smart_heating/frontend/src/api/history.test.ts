import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import * as api from './history'

vi.mock('axios')
const mockedAxios = axios as unknown as jest.Mocked<typeof axios>

describe('API - History', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getHistory constructs URL params correctly', async () => {
    mockedAxios.get = vi
      .fn()
      .mockResolvedValue({ data: { area_id: 'a1', entries: [], count: 0 } }) as any
    await api.getHistory('a1', { hours: 2, startTime: '2024-01-01', endTime: '2024-01-02' })
    expect(mockedAxios.get).toHaveBeenCalledWith(
      '/api/smart_heating/areas/a1/history?hours=2&start_time=2024-01-01&end_time=2024-01-02',
    )
  })

  it('history config and actions', async () => {
    mockedAxios.get = vi.fn().mockResolvedValue({
      data: {
        retention_days: 30,
        storage_backend: 'json',
        record_interval_seconds: 60,
        record_interval_minutes: 1,
      },
    }) as any
    const cfg = await api.getHistoryConfig()
    expect(cfg.retention_days).toBe(30)

    mockedAxios.post = vi.fn().mockResolvedValue({ data: {} }) as any
    await api.setHistoryRetention(15)
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/smart_heating/history/config', {
      retention_days: 15,
    })
  })
})
