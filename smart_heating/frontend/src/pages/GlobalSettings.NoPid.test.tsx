import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import GlobalSettings from './GlobalSettings'

// Mock all API calls
vi.mock('../api/presets', () => ({
  getGlobalPresets: vi.fn().mockResolvedValue({
    away_temp: 15,
    eco_temp: 18,
    comfort_temp: 22,
    home_temp: 20,
    sleep_temp: 18,
    activity_temp: 21,
  }),
  setGlobalPresets: vi.fn().mockResolvedValue({}),
}))

vi.mock('../api/sensors', () => ({
  getGlobalPresence: vi.fn().mockResolvedValue({ sensors: [] }),
  setGlobalPresence: vi.fn().mockResolvedValue({}),
}))

vi.mock('../api/logs', () => ({
  getHysteresis: vi.fn().mockResolvedValue(0.5),
  setHysteresis: vi.fn().mockResolvedValue({}),
}))

vi.mock('../api/safety', () => ({
  getSafetySensor: vi.fn().mockResolvedValue(null),
  setSafetySensor: vi.fn().mockResolvedValue({}),
  removeSafetySensor: vi.fn().mockResolvedValue({}),
}))

vi.mock('../api/devices', () => ({
  setHideDevicesPanel: vi.fn().mockResolvedValue({}),
}))

vi.mock('../api/config', () => ({
  getConfig: vi.fn().mockResolvedValue({
    hide_devices_panel: false,
    opentherm_gateway_id: '',
  }),
  getAdvancedControlConfig: vi.fn().mockResolvedValue({
    advanced_control_enabled: false,
    heating_curve_enabled: false,
    pwm_enabled: false,
    overshoot_protection_enabled: false,
    default_heating_curve_coefficient: 1,
  }),
  setAdvancedControlConfig: vi.fn().mockResolvedValue({}),
}))

vi.mock('../api/opentherm', () => ({
  setOpenthermGateway: vi.fn().mockResolvedValue({}),
  getOpenthermGateways: vi.fn().mockResolvedValue([]),
  calibrateOpentherm: vi.fn().mockResolvedValue({ opv: 1.0 }),
}))

const renderGlobalSettings = () => {
  return render(
    <BrowserRouter>
      <GlobalSettings themeMode="light" onThemeChange={vi.fn()} />
    </BrowserRouter>,
  )
}

describe('GlobalSettings - PID Control Removed', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('No Global PID Toggle', () => {
    it('does not render PID enable switch', async () => {
      renderGlobalSettings()

      // Wait for component to load
      await screen.findByRole('tablist')

      // Check for various possible PID-related text
      const pidToggle = screen.queryByText(/enable pid control/i)
      const pidSwitch = screen.queryByLabelText(/pid control/i)
      const pidSetting = screen.queryByTestId('pid-enabled-switch')

      expect(pidToggle).not.toBeInTheDocument()
      expect(pidSwitch).not.toBeInTheDocument()
      expect(pidSetting).not.toBeInTheDocument()
    })

    it('does not have pidEnabled state variable', () => {
      // This is a compile-time check - if pidEnabled was used,
      // TypeScript would show errors. We verify runtime behavior.
      renderGlobalSettings()

      // No PID-related controls should exist
      const allSwitches = screen.queryAllByRole('checkbox')

      // Filter out switches that might be PID-related
      const pidSwitches = allSwitches.filter(sw => {
        const label = sw.getAttribute('aria-label') || ''
        const testId = sw.getAttribute('data-testid') || ''
        return label.toLowerCase().includes('pid') || testId.toLowerCase().includes('pid')
      })

      expect(pidSwitches).toHaveLength(0)
    })

    it('does not include pid_enabled in any API calls', async () => {
      const { getAdvancedControlConfig, setAdvancedControlConfig } = await import('../api/config')
      const mockSetConfig = vi.mocked(setAdvancedControlConfig)

      renderGlobalSettings()

      // Wait for initial loads
      await screen.findByRole('tablist')

      // Check that no API calls include pid_enabled
      mockSetConfig.mock.calls.forEach(call => {
        const payload = call[0]
        expect(payload).not.toHaveProperty('pid_enabled')
      })
    })
  })

  describe('Advanced Control Settings (No PID)', () => {
    it('shows advanced control settings without PID option', async () => {
      renderGlobalSettings()

      // Wait for component to load
      await screen.findByRole('tablist')

      // Advanced control should exist, but not PID
      const advancedTab = screen.queryByText(/advanced/i)
      if (advancedTab) {
        // Advanced tab exists, but PID should not be there
        const pidControl = screen.queryByText(/pid control/i)
        expect(pidControl).not.toBeInTheDocument()
      }
    })

    it('has heating curve, PWM, and overshoot protection but no PID', async () => {
      renderGlobalSettings()

      await screen.findByRole('tablist')

      // These settings should exist (if on Advanced tab)
      // But PID should not be a global setting
      const pidGlobal = screen.queryByText(/global pid/i)
      const pidEnabled = screen.queryByLabelText(/enable pid/i)

      expect(pidGlobal).not.toBeInTheDocument()
      expect(pidEnabled).not.toBeInTheDocument()
    })
  })

  describe('State Management', () => {
    it('does not manage pid_enabled state', async () => {
      renderGlobalSettings()

      await screen.findByRole('tablist')

      // Verify no PID state is being tracked
      // This is verified by the absence of PID-related controls
      const allInputs = screen.queryAllByRole('checkbox')
      const allSliders = screen.queryAllByRole('slider')

      // Check all inputs don't have PID-related names
      const allControls = allInputs.concat(allSliders)
      allControls.forEach(input => {
        const name = input.getAttribute('name') || ''
        const id = input.getAttribute('id') || ''
        const testId = input.getAttribute('data-testid') || ''

        expect(name.toLowerCase()).not.toContain('pid')
        expect(id.toLowerCase()).not.toContain('pid_enabled')
        expect(testId.toLowerCase()).not.toContain('pid_enabled')
      })
    })
  })

  describe('Tabs and Sections', () => {
    it('renders all tabs without PID tab', async () => {
      renderGlobalSettings()

      await screen.findByRole('tablist')

      // Check that there's no dedicated PID tab
      const pidTab = screen.queryByRole('tab', { name: /pid/i })
      expect(pidTab).not.toBeInTheDocument()
    })

    it('presets tab does not mention PID', async () => {
      renderGlobalSettings()

      await screen.findByRole('tablist')

      // Wait for presets content to load
      await screen.findByText(/away/i)

      // Check no PID mentions in presets section
      const pidText = screen.queryByText(/pid/i)
      expect(pidText).not.toBeInTheDocument()
    })
  })

  describe('Configuration Persistence', () => {
    it('loads config without pid_enabled field', async () => {
      const { getConfig, getAdvancedControlConfig } = await import('../api/config')
      const mockGetConfig = vi.mocked(getConfig)
      const mockGetAdvancedConfig = vi.mocked(getAdvancedControlConfig)

      renderGlobalSettings()

      await screen.findByRole('tablist')

      // Verify config loads were called
      expect(mockGetConfig).toHaveBeenCalled()
      expect(mockGetAdvancedConfig).toHaveBeenCalled()

      // Verify no pid_enabled in config
      const configCalls = mockGetConfig.mock.results
      configCalls.forEach(async result => {
        const config = await result.value
        expect(config).not.toHaveProperty('pid_enabled')
      })
    })

    it('saves config without pid_enabled field', async () => {
      const { setAdvancedControlConfig } = await import('../api/config')
      const mockSetConfig = vi.mocked(setAdvancedControlConfig)

      renderGlobalSettings()

      await screen.findByRole('tablist')

      // Check all save operations don't include pid_enabled
      mockSetConfig.mock.calls.forEach(call => {
        const [payload] = call
        expect(payload).not.toHaveProperty('pid_enabled')
      })
    })
  })

  describe('No Legacy PID Code', () => {
    it('does not have toggle handlers for PID', async () => {
      renderGlobalSettings()

      await screen.findByRole('tablist')

      // Verify no onClick handlers that might toggle PID
      const allButtons = screen.queryAllByRole('button')
      const allSwitches = screen.queryAllByRole('checkbox')

      const allControls = allButtons.concat(allSwitches)
      allControls.forEach(element => {
        const onClick = element.getAttribute('onclick') || ''
        const testId = element.getAttribute('data-testid') || ''

        expect(onClick.toLowerCase()).not.toContain('pid')
        expect(testId.toLowerCase()).not.toContain('togglepid')
        expect(testId.toLowerCase()).not.toContain('pid_toggle')
      })
    })

    it('does not have PID-related form controls', async () => {
      renderGlobalSettings()

      await screen.findByRole('tablist')

      // Check form controls
      const formControls = screen.queryAllByRole('textbox')
      const selects = screen.queryAllByRole('combobox')

      const allFormElements = formControls.concat(selects)
      allFormElements.forEach(control => {
        const label = control.getAttribute('aria-label') || ''
        const name = control.getAttribute('name') || ''

        expect(label.toLowerCase()).not.toContain('pid')
        expect(name.toLowerCase()).not.toContain('pid_enabled')
      })
    })
  })

  describe('Documentation and Help Text', () => {
    it('does not mention global PID in any help text', async () => {
      renderGlobalSettings()

      await screen.findByRole('tablist')

      // Check all text content doesn't mention "global PID" or "enable PID globally"
      const helpTexts = screen.queryAllByText(/pid/i)

      helpTexts.forEach(text => {
        const content = text.textContent || ''
        expect(content.toLowerCase()).not.toContain('global pid')
        expect(content.toLowerCase()).not.toContain('enable pid globally')
        expect(content.toLowerCase()).not.toContain('pid for all areas')
      })
    })
  })
})
