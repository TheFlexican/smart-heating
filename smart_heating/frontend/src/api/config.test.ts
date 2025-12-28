import { describe, it, expect, vi, beforeEach } from 'vitest'
import { apiClient } from './client'
import * as cfg from './config'

vi.mock('./client')
const mockedClient = vi.mocked(apiClient)

describe('API - Config', () => {
  beforeEach(() => vi.clearAllMocks())

  it('status/config/advanced and entity/binary/weather endpoints', async () => {
    mockedClient.get.mockResolvedValue({ data: { status: { ok: true } } } as any)
    const status = await cfg.getStatus()
    expect(status.status.ok).toBe(true)

    mockedClient.get.mockResolvedValue({ data: { config: { v: 1 } } } as any)
    const config = await cfg.getConfig()
    expect(config.config.v).toBe(1)

    mockedClient.get.mockResolvedValue({ data: { advanced: true } } as any)
    const advanced = await cfg.getAdvancedControlConfig()
    expect(advanced.advanced).toBe(true)

    mockedClient.post.mockResolvedValue({ data: {} } as any)
    await cfg.setAdvancedControlConfig({ test: true })
    expect(mockedClient.post).toHaveBeenCalledWith('/config/advanced_control', {
      test: true,
    })

    mockedClient.get.mockResolvedValue({ data: { state: 'on' } } as any)
    const ent = await cfg.getEntityState('binary_sensor.test')
    expect(ent.state).toBe('on')

    mockedClient.get.mockResolvedValue({ data: { entities: [] } } as any)
    await cfg.getBinarySensorEntities()
    await cfg.getWeatherEntities()
  })

  it('set frost protection calls API', async () => {
    mockedClient.post.mockResolvedValue({ data: {} } as any)
    await cfg.setFrostProtection(true, 3)
    expect(mockedClient.post).toHaveBeenCalledWith('/frost_protection', {
      enabled: true,
      temperature: 3,
    })
  })
})
