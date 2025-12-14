import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import * as cfg from './config'

vi.mock('axios')
const mockedAxios = axios as unknown as jest.Mocked<typeof axios>

describe('API - Config', () => {
  beforeEach(() => vi.clearAllMocks())

  it('status/config/advanced and entity/binary/weather endpoints', async () => {
    mockedAxios.get = vi.fn().mockResolvedValue({ data: { status: { ok: true } } }) as any
    const status = await cfg.getStatus()
    expect(status.status.ok).toBe(true)

    mockedAxios.get = vi.fn().mockResolvedValue({ data: { config: { v: 1 } } }) as any
    const config = await cfg.getConfig()
    expect(config.config.v).toBe(1)

    mockedAxios.get = vi.fn().mockResolvedValue({ data: { advanced: true } }) as any
    const advanced = await cfg.getAdvancedControlConfig()
    expect(advanced.advanced).toBe(true)

    mockedAxios.post = vi.fn().mockResolvedValue({ data: {} }) as any
    await cfg.setAdvancedControlConfig({ test: true })
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/smart_heating/config/advanced_control', { test: true })

    mockedAxios.get = vi.fn().mockResolvedValue({ data: { state: 'on' } }) as any
    const ent = await cfg.getEntityState('binary_sensor.test')
    expect(ent.state).toBe('on')

    mockedAxios.get = vi.fn().mockResolvedValue({ data: { entities: [] } }) as any
    await cfg.getBinarySensorEntities()
    await cfg.getWeatherEntities()
  })

  it('set frost protection calls API', async () => {
    mockedAxios.post = vi.fn().mockResolvedValue({ data: {} }) as any
    await cfg.setFrostProtection(true, 3)
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/smart_heating/frost_protection', { enabled: true, temperature: 3 })
  })
})
