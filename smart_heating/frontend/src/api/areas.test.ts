import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import * as api from './areas'

vi.mock('axios')
const mockedAxios = axios as unknown as jest.Mocked<typeof axios>

describe('API - Areas', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getZones returns areas from API', async () => {
    mockedAxios.get = vi.fn().mockResolvedValue({ data: { areas: [{ id: 'a1', name: 'Test' }] } }) as any
    const result = await api.getZones()
    expect(result).toEqual([{ id: 'a1', name: 'Test' }])
    expect(mockedAxios.get).toHaveBeenCalledWith('/api/smart_heating/areas')
  })

  it('setBoostMode posts duration and optional temp', async () => {
    mockedAxios.post = vi.fn().mockResolvedValue({ data: {} }) as any
    await api.setBoostMode('area1', 10, 22)
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/smart_heating/areas/area1/boost', { duration: 10, temperature: 22 })
    await api.setBoostMode('area1', 5)
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/smart_heating/areas/area1/boost', { duration: 5 })
  })

  it('copySchedule includes optional arrays', async () => {
    mockedAxios.post = vi.fn().mockResolvedValue({ data: {} }) as any
    await api.copySchedule('src', 'dst', ['Mon'], ['Tue'])
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/smart_heating/copy_schedule', {
      source_area_id: 'src',
      target_area_id: 'dst',
      source_days: ['Mon'],
      target_days: ['Tue']
    })
  })
})
