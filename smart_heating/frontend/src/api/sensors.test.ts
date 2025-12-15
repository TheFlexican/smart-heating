import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import * as s from './sensors'

vi.mock('axios')
const mockedAxios = axios as unknown as jest.Mocked<typeof axios>

describe('API - Sensors', () => {
  beforeEach(() => vi.clearAllMocks())

  it('add/remove window sensor, presence sensor and global presence', async () => {
    mockedAxios.post = vi.fn().mockResolvedValue({ data: {} }) as any
    await s.addWindowSensor('a1', { entity_id: 'sensor.w1' } as any)
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/smart_heating/areas/a1/window_sensors', {
      entity_id: 'sensor.w1',
    })
    mockedAxios.delete = vi.fn().mockResolvedValue({ data: {} }) as any
    await s.removeWindowSensor('a1', 'sensor.w1')
    expect(mockedAxios.delete).toHaveBeenCalledWith(
      '/api/smart_heating/areas/a1/window_sensors/sensor.w1'
    )

    mockedAxios.post = vi.fn().mockResolvedValue({ data: {} }) as any
    await s.addPresenceSensor('a1', { entity_id: 'sensor.p1' } as any)
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/smart_heating/areas/a1/presence_sensors', {
      entity_id: 'sensor.p1',
    })
    mockedAxios.delete = vi.fn().mockResolvedValue({ data: {} }) as any
    await s.removePresenceSensor('a1', 'sensor.p1')
    expect(mockedAxios.delete).toHaveBeenCalledWith(
      '/api/smart_heating/areas/a1/presence_sensors/sensor.p1'
    )

    mockedAxios.get = vi.fn().mockResolvedValue({ data: { sensors: [] } }) as any
    const gp = await s.getGlobalPresence()
    expect(gp.sensors).toEqual([])
    mockedAxios.post = vi.fn().mockResolvedValue({ data: {} }) as any
    await s.setGlobalPresence([{ entity_id: 'sensor.p1' } as any])
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/smart_heating/global_presence', {
      sensors: [{ entity_id: 'sensor.p1' }],
    })
  })
})
