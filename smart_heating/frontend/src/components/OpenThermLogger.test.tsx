import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import OpenThermLogger from './OpenThermLogger'
import * as openthermApi from '../api/opentherm'

vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string, v?: any) => k }) }))

vi.mock('../api/opentherm', () => ({
  getOpenThermLogs: vi.fn().mockResolvedValue({ logs: [{ timestamp: '2024-01-01T00:00:00Z', event_type: 'gateway_info', data: {}, message: 'ok' }] }),
  getOpenthermGateways: vi.fn().mockResolvedValue([{ gateway_id: 'g1', title: 'G1' }]),
  getOpenThermSensorStates: vi.fn().mockResolvedValue({ control_setpoint: 22.5, modulation_level: 55, flame_on: true }),
  getOpenThermCapabilities: vi.fn().mockResolvedValue({ capabilities: {} }),
  discoverOpenThermCapabilities: vi.fn().mockResolvedValue({ capabilities: {} }),
  clearOpenThermLogs: vi.fn().mockResolvedValue({ success: true }),
}))

describe('OpenThermLogger', () => {
  beforeEach(() => vi.clearAllMocks())

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
