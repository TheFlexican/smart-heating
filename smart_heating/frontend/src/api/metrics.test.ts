import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import * as metrics from './metrics'

vi.mock('axios')
const mockedAxios = axios as unknown as jest.Mocked<typeof axios>

describe('API - Metrics', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getAdvancedMetrics builds params', async () => {
    mockedAxios.get = vi.fn().mockResolvedValue({ data: {} }) as any
    await metrics.getAdvancedMetrics(7)
    expect(mockedAxios.get).toHaveBeenCalledWith('/api/smart_heating/metrics/advanced?days=7')
    await metrics.getAdvancedMetrics(1, 'a1')
    expect(mockedAxios.get).toHaveBeenCalledWith(
      '/api/smart_heating/metrics/advanced?days=1&area_id=a1'
    )
  })
})
