import { describe, it, expect, vi, beforeEach } from 'vitest'
import { apiClient } from './client'
import * as metrics from './metrics'

vi.mock('./client')
const mockedClient = vi.mocked(apiClient)

describe('API - Metrics', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getAdvancedMetrics builds params with minutes (default)', async () => {
    mockedClient.get.mockResolvedValue({ data: {} } as any)
    await metrics.getAdvancedMetrics(5)
    expect(mockedClient.get).toHaveBeenCalledWith('/metrics/advanced?minutes=5')
    await metrics.getAdvancedMetrics(1, 'a1')
    expect(mockedClient.get).toHaveBeenCalledWith('/metrics/advanced?minutes=1&area_id=a1')
  })

  it('getAdvancedMetrics builds params with days when forceDays is true', async () => {
    mockedClient.get.mockResolvedValue({ data: {} } as any)
    await metrics.getAdvancedMetrics(1, undefined, true)
    expect(mockedClient.get).toHaveBeenCalledWith('/metrics/advanced?days=1')
    await metrics.getAdvancedMetrics(3, 'a1', true)
    expect(mockedClient.get).toHaveBeenCalledWith('/metrics/advanced?days=3&area_id=a1')
  })

  it('getAdvancedMetrics builds params with hours when forceHours is true', async () => {
    mockedClient.get.mockResolvedValue({ data: {} } as any)
    await metrics.getAdvancedMetrics(1, undefined, false, true)
    expect(mockedClient.get).toHaveBeenCalledWith('/metrics/advanced?hours=1')
    await metrics.getAdvancedMetrics(2, 'a1', false, true)
    expect(mockedClient.get).toHaveBeenCalledWith('/metrics/advanced?hours=2&area_id=a1')
    await metrics.getAdvancedMetrics(5, undefined, false, true)
    expect(mockedClient.get).toHaveBeenCalledWith('/metrics/advanced?hours=5')
  })

  it('forceHours takes precedence over forceDays', async () => {
    mockedClient.get.mockResolvedValue({ data: {} } as any)
    await metrics.getAdvancedMetrics(1, undefined, true, true)
    expect(mockedClient.get).toHaveBeenCalledWith('/metrics/advanced?hours=1')
  })
})
