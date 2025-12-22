import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import OpenThermLogger from './OpenThermLogger'
import * as openthermApi from '../../api/opentherm'

vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string, _v?: any) => k }) }))

beforeEach(() => {
  vi.spyOn(openthermApi, 'getOpenThermLogs').mockResolvedValue({
    logs: [
      { timestamp: '2024-01-01T00:00:00Z', event_type: 'gateway_info', data: {}, message: 'ok' },
    ],
  })
  vi.spyOn(openthermApi, 'getOpenthermGateways').mockResolvedValue([
    { gateway_id: 'g1', title: 'G1' },
  ])
  vi.spyOn(openthermApi, 'getOpenThermSensorStates').mockResolvedValue({
    control_setpoint: 21.5,
    modulation_level: 35,
    ch_water_temp: 45,
    return_water_temp: 30.5,
    ch_pressure: 1.95,
    room_temp: 21,
    ch_active: true,
    flame_on: true,
  })
  vi.spyOn(openthermApi, 'getOpenThermCapabilities').mockResolvedValue({ capabilities: {} })
  vi.spyOn(openthermApi, 'discoverOpenThermCapabilities').mockResolvedValue({ capabilities: {} })
  vi.spyOn(openthermApi, 'clearOpenThermLogs').mockResolvedValue({ success: true })
})

describe('OpenThermLogger', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders key OpenTherm elements with testids', async () => {
    const { findByTestId } = render(<OpenThermLogger />)

    // Wait for initial content to render
    expect(await findByTestId('opentherm-content')).toBeTruthy()

    expect(await findByTestId('opentherm-control-setpoint')).toBeTruthy()
    expect(await findByTestId('opentherm-modulation')).toBeTruthy()
    expect(await findByTestId('opentherm-ch-water')).toBeTruthy()
    expect(await findByTestId('opentherm-return-water')).toBeTruthy()
    expect(await findByTestId('opentherm-system-pressure')).toBeTruthy()
    expect(await findByTestId('opentherm-room-temperature')).toBeTruthy()
    expect(await findByTestId('opentherm-boiler-errors')).toBeTruthy()
  })

  it('loads data on mount', async () => {
    render(<OpenThermLogger />)

    // Verify all API calls made on load
    await waitFor(() => {
      expect(openthermApi.getOpenThermLogs).toHaveBeenCalled()
      expect(openthermApi.getOpenthermGateways).toHaveBeenCalled()
      expect(openthermApi.getOpenThermSensorStates).toHaveBeenCalled()
    })
  })

  it('calls discover and clear APIs when buttons clicked', async () => {
    const user = userEvent.setup()

    render(<OpenThermLogger />)
    await waitFor(() => expect(openthermApi.getOpenThermLogs).toHaveBeenCalled())

    await user.click(screen.getByRole('button', { name: 'opentherm.discoverCapabilities' }))
    expect(openthermApi.discoverOpenThermCapabilities).toHaveBeenCalled()

    await user.click(screen.getByRole('button', { name: /common.clear/ }))
    expect(openthermApi.clearOpenThermLogs).toHaveBeenCalled()
  })
})
