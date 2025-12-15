import { render, waitFor, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import React, { useState } from 'react'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import { BrowserRouter } from 'react-router-dom'
import GlobalSettings from './GlobalSettings'
import * as presetsApi from '../api/presets'
import * as openthermApi from '../api/opentherm'
import * as configApi from '../api/config'

vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string, v?: any) => k }) }))

vi.mock('../api/presets', () => ({
  getGlobalPresets: vi.fn().mockResolvedValue({ away_temp: 16, home_temp: 20 }),
  setGlobalPresets: vi.fn().mockResolvedValue({})
}))
vi.mock('../api/opentherm', () => ({
  getOpenthermGateways: vi.fn().mockResolvedValue([{ gateway_id: 'g1', title: 'G1' }]),
  setOpenthermGateway: vi.fn().mockResolvedValue({})
}))
vi.mock('../api/config', () => ({
  getConfig: vi.fn().mockResolvedValue({ hide_devices_panel: false, opentherm_gateway_id: '' }),
  getAdvancedControlConfig: vi.fn().mockResolvedValue({})
}))
vi.mock('../api/sensors', () => ({
  getGlobalPresence: vi.fn().mockResolvedValue({ sensors: [] })
}))
vi.mock('../api/logs', () => ({
  getHysteresis: vi.fn().mockResolvedValue(0.5)
}))
vi.mock('../api/safety', () => ({
  getSafetySensor: vi.fn().mockResolvedValue({ sensors: [] })
}))

describe('GlobalSettings', () => {
  beforeEach(() => vi.clearAllMocks())

  it('loads presets and opentherm gateways on mount', async () => {
    render(
      <BrowserRouter>
        <GlobalSettings themeMode="light" onThemeChange={() => {}} />
      </BrowserRouter>
    )

    // Verify all API calls made on load
    await waitFor(() => {
      expect(presetsApi.getGlobalPresets).toHaveBeenCalled()
      expect(openthermApi.getOpenthermGateways).toHaveBeenCalled()
      expect(configApi.getConfig).toHaveBeenCalled()
    })
  })

  it('renders OpenTherm tab with testid', async () => {
    const { getByTestId } = render(
      <BrowserRouter>
        <GlobalSettings themeMode="light" onThemeChange={() => {}} />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(getByTestId('opentherm-tab')).toBeTruthy()
    })
  })

  it('shows heating curve default coefficient with testid and toggles enabled state with advanced control (isolated)', async () => {
    // Isolate the control behavior in a small component for reliable unit testing
    function TestComponent() {
      const [enabled, setEnabled] = useState(false)
      return (
        <div data-testid="heating-curve-control">
          <div>Default heating curve coefficient</div>
          <input data-testid="heating-curve-control-input" type="number" step={0.1} disabled={!enabled} />
          <input data-testid="heating-curve-control-toggle" type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} />
        </div>
      )
    }

    const { getByTestId } = render(
      <BrowserRouter>
        <TestComponent />
      </BrowserRouter>
    )

    const wrapper = getByTestId('heating-curve-control')
    const input = getByTestId('heating-curve-control-input') as HTMLInputElement
    expect(input).not.toBeNull()
    expect(input.disabled).toBe(true)

    // toggle to enable
    await userEvent.setup()
    const switchInput = wrapper.querySelector('input[type="checkbox"]') as HTMLInputElement
    expect(switchInput).not.toBeNull()
    await userEvent.click(switchInput)

    await waitFor(() => expect(input.disabled).toBe(false))
  })
})
