import { describe, it, expect, vi, beforeEach } from 'vitest'
import { apiClient } from './client'
import * as api from './areas'

vi.mock('./client')
const mockedClient = vi.mocked(apiClient)

describe('API - Areas', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getZones returns areas from API', async () => {
    mockedClient.get.mockResolvedValue({ data: { areas: [{ id: 'a1', name: 'Test' }] } } as any)
    const result = await api.getZones()
    expect(result).toEqual([{ id: 'a1', name: 'Test' }])
    expect(mockedClient.get).toHaveBeenCalledWith('/areas')
  })

  it('setBoostMode posts duration and optional temp', async () => {
    mockedClient.post.mockResolvedValue({ data: {} } as any)
    await api.setBoostMode('area1', 10, 22)
    expect(mockedClient.post).toHaveBeenCalledWith('/areas/area1/boost', {
      duration: 10,
      temperature: 22,
    })
    await api.setBoostMode('area1', 5)
    expect(mockedClient.post).toHaveBeenCalledWith('/areas/area1/boost', {
      duration: 5,
    })
  })

  it('copySchedule includes optional arrays', async () => {
    mockedClient.post.mockResolvedValue({ data: {} } as any)
    await api.copySchedule('src', 'dst', ['Mon'], ['Tue'])
    expect(mockedClient.post).toHaveBeenCalledWith('/copy_schedule', {
      source_area_id: 'src',
      target_area_id: 'dst',
      source_days: ['Mon'],
      target_days: ['Tue'],
    })
  })
})
