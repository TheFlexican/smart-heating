import { describe, it, expect, vi, beforeEach } from 'vitest'
import { apiClient } from './client'
import * as metrics from './metrics'

vi.mock('./client')
const mockedClient = vi.mocked(apiClient)

describe('API - Metrics', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getAdvancedMetrics builds params', async () => {
    mockedClient.get.mockResolvedValue({ data: {} } as any)
    await metrics.getAdvancedMetrics(5)
    expect(mockedClient.get).toHaveBeenCalledWith('/metrics/advanced?minutes=5')
    await metrics.getAdvancedMetrics(1, 'a1')
    expect(mockedClient.get).toHaveBeenCalledWith('/metrics/advanced?minutes=1&area_id=a1')
  })
})
