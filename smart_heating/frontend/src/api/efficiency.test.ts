import { describe, it, expect, vi, beforeEach } from 'vitest'
import { apiClient } from './client'
import * as efficiency from './efficiency'

vi.mock('./client')
const mockedClient = vi.mocked(apiClient)

describe('API - Efficiency', () => {
  beforeEach(() => vi.clearAllMocks())

  it('efficiency and comparison endpoints', async () => {
    mockedClient.get.mockResolvedValue({ data: { report: true } } as any)
    await efficiency.getEfficiencyReport('a1')
    expect(mockedClient.get).toHaveBeenCalledWith('/efficiency/report/a1?period=week')
    await efficiency.getAllAreasEfficiency('day')
    expect(mockedClient.get).toHaveBeenCalledWith('/efficiency/all_areas?period=day')
    await efficiency.getComparison('month')
    expect(mockedClient.get).toHaveBeenCalledWith('/comparison/month')
    mockedClient.post.mockResolvedValue({ data: {} } as any)
    await efficiency.getCustomComparison('2020-01-01', '2020-01-02', '2021-01-01', '2021-01-02')
    expect(mockedClient.post).toHaveBeenCalledWith('/comparison/custom', {
      start_a: '2020-01-01',
      end_a: '2020-01-02',
      start_b: '2021-01-01',
      end_b: '2021-01-02',
    })
  })
})
