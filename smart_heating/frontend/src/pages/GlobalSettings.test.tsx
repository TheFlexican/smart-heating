import { render, waitFor } from '@testing-library/react'
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
})
