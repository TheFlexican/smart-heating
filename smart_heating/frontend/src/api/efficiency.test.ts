import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import * as efficiency from './efficiency'

vi.mock('axios')
const mockedAxios = axios as unknown as jest.Mocked<typeof axios>

describe('API - Efficiency', () => {
  beforeEach(() => vi.clearAllMocks())

  it('efficiency and comparison endpoints', async () => {
    mockedAxios.get = vi.fn().mockResolvedValue({ data: { report: true } }) as any
    await efficiency.getEfficiencyReport('a1')
    expect(mockedAxios.get).toHaveBeenCalledWith(
      '/api/smart_heating/efficiency/report/a1?period=week',
    )
    await efficiency.getAllAreasEfficiency('day')
    expect(mockedAxios.get).toHaveBeenCalledWith(
      '/api/smart_heating/efficiency/all_areas?period=day',
    )
    await efficiency.getComparison('month')
    expect(mockedAxios.get).toHaveBeenCalledWith('/api/smart_heating/comparison/month')
    mockedAxios.post = vi.fn().mockResolvedValue({ data: {} }) as any
    await efficiency.getCustomComparison('2020-01-01', '2020-01-02', '2021-01-01', '2021-01-02')
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/smart_heating/comparison/custom', {
      start_a: '2020-01-01',
      end_a: '2020-01-02',
      start_b: '2021-01-01',
      end_b: '2021-01-02',
    })
  })
})
