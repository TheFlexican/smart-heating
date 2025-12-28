import { describe, it, expect, vi, beforeEach } from 'vitest'
import { apiClient } from './client'
import * as api from './opentherm'

vi.mock('./client')
const mockedClient = vi.mocked(apiClient)

describe('API - OpenTherm', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getOpenThermSensorStates maps states and parsers', async () => {
    const responses = (id: string) => {
      const map: Record<string, any> = {
        'sensor.opentherm_ketel_regel_instelpunt_1': { data: { state: '22.5' } },
        'sensor.opentherm_ketel_relatief_modulatieniveau': { data: { state: '55' } },
        'binary_sensor.opentherm_ketel_vlam': { data: { state: 'on' } },
        'binary_sensor.opentherm_ketel_centrale_verwarming_1': { data: { state: 'off' } },
      }
      return map[id] || { data: { state: '0' } }
    }
    mockedClient.get.mockImplementation((url: string) => {
      const id = url.split('/').pop() || ''
      return Promise.resolve(responses(id)) as any
    })

    const result = await api.getOpenThermSensorStates()
    expect(result.control_setpoint).toBeCloseTo(22.5)
    expect(result.modulation_level).toBeCloseTo(55)
    expect(result.flame_on).toBe(true)
    expect(result.ch_active).toBe(false)
  })

  it('getOpenthermGateways and engineering endpoints', async () => {
    mockedClient.get.mockResolvedValue({
      data: { gateways: [{ gateway_id: 'g1', title: 'G1' }] },
    } as any)
    const gws = await api.getOpenthermGateways()
    expect(gws[0].gateway_id).toBe('g1')

    mockedClient.get.mockResolvedValue({ data: { capabilities: {} } } as any)
    const caps = await api.getOpenThermCapabilities()
    expect(caps).toBeDefined()

    mockedClient.post.mockResolvedValue({ data: { success: true } } as any)
    await api.discoverOpenThermCapabilities()
    await api.clearOpenThermLogs()
    expect(mockedClient.post).toHaveBeenCalled()
  })
})
