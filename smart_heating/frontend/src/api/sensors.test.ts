import { describe, it, expect, vi, beforeEach } from 'vitest'
import { apiClient } from './client'
import * as s from './sensors'

vi.mock('./client')
const mockedClient = vi.mocked(apiClient)

describe('API - Sensors', () => {
  beforeEach(() => vi.clearAllMocks())

  it('add/remove window sensor, presence sensor and global presence', async () => {
    mockedClient.post.mockResolvedValue({ data: {} } as any)
    await s.addWindowSensor('a1', { entity_id: 'sensor.w1' } as any)
    expect(mockedClient.post).toHaveBeenCalledWith('/areas/a1/window_sensors', {
      entity_id: 'sensor.w1',
    })

    mockedClient.delete.mockResolvedValue({ data: {} } as any)
    await s.removeWindowSensor('a1', 'sensor.w1')
    expect(mockedClient.delete).toHaveBeenCalledWith('/areas/a1/window_sensors/sensor.w1')

    mockedClient.post.mockResolvedValue({ data: {} } as any)
    await s.addPresenceSensor('a1', { entity_id: 'sensor.p1' } as any)
    expect(mockedClient.post).toHaveBeenCalledWith('/areas/a1/presence_sensors', {
      entity_id: 'sensor.p1',
    })

    mockedClient.delete.mockResolvedValue({ data: {} } as any)
    await s.removePresenceSensor('a1', 'sensor.p1')
    expect(mockedClient.delete).toHaveBeenCalledWith('/areas/a1/presence_sensors/sensor.p1')

    mockedClient.get.mockResolvedValue({ data: { sensors: [] } } as any)
    const gp = await s.getGlobalPresence()
    expect(gp.sensors).toEqual([])

    mockedClient.post.mockResolvedValue({ data: {} } as any)
    await s.setGlobalPresence([{ entity_id: 'sensor.p1' } as any])
    expect(mockedClient.post).toHaveBeenCalledWith('/global_presence', {
      sensors: [{ entity_id: 'sensor.p1' }],
    })
  })
})
