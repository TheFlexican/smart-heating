import { render, screen } from '@testing-library/react'
import { vi, it, expect } from 'vitest'
import ZoneCard from './ZoneCard'

// Mock react-i18next to provide a basic translation function
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (k: string, v?: any) => {
      if (v && v.temp) return `${v.temp}°C`
      if (k.startsWith('presets.')) return k.split('.')[1].toUpperCase()
      return k
    },
  }),
}))

// Mock react-router-dom navigate to prevent side effects
vi.mock('react-router-dom', () => ({ useNavigate: () => vi.fn() }))

// Mock API functions called by ZoneCard
vi.mock('../api/areas', () => ({
  setZoneTemperature: vi.fn(),
  removeDeviceFromZone: vi.fn(),
  hideZone: vi.fn(),
  unhideZone: vi.fn(),
  setManualOverride: vi.fn(),
  setBoostMode: vi.fn(),
  cancelBoost: vi.fn(),
}))
vi.mock('../api/config', () => ({ getEntityState: vi.fn().mockResolvedValue({ state: 'home' }) }))

const baseArea = {
  id: 'area_1',
  name: 'Living Room',
  enabled: false,
  state: 'off',
  target_temperature: 20,
  effective_target_temperature: 23.5,
  preset_mode: 'comfort',
  manual_override: true,
  presence_sensors: [],
  boost_mode_active: false,
  devices: [],
  current_temperature: 19.2,
}

it('hides preset chip and shows base temperature when area is disabled/off', () => {
  render(<ZoneCard area={baseArea as any} onUpdate={() => {}} />)

  // Preset chip should not be present
  expect(screen.queryByText('COMFORT')).toBeNull()

  // Displayed temperature should be the base target temperature
  expect(screen.queryByText('20°C')).not.toBeNull()
})

it('shows preset chip and effective temperature when area is enabled', () => {
  const enabledArea = { ...baseArea, enabled: true, state: 'idle', manual_override: false }
  render(<ZoneCard area={enabledArea as any} onUpdate={() => {}} />)

  // Preset chip should exist
  expect(screen.queryByText('COMFORT')).not.toBeNull()

  // Displayed temperature should be the effective target temperature
  expect(screen.queryByText('23.5°C')).not.toBeNull()
})

it('treats non-boolean `enabled` as falsy and disables controls', () => {
  const area: any = {
    id: 'area1',
    name: 'Living Room',
    enabled: 'false', // string value that should be coerced to boolean(false)
    state: 'idle',
    manual_override: false,
    preset_mode: 'none',
    effective_target_temperature: null,
    target_temperature: 21,
    devices: [],
    presence_sensors: [],
    boost_mode_active: false,
    boost_temp: null,
    boost_duration: null,
    heating_type: 'radiator',
    hvac_mode: undefined,
    hidden: false,
  }

  render(<ZoneCard area={area} onUpdate={vi.fn()} />)

  // Slider should be present and have disabled styling when area is disabled
  const slider = screen.getByTestId('temperature-slider')
  expect(slider.classList.contains('Mui-disabled')).toBe(true)

  // Preset badge should not be rendered for disabled area
  const badge = screen.queryByTestId('preset-mode-badge')
  expect(badge).toBeNull()

  // Target temperature display should still show the configured target
  const display = screen.getByTestId('target-temperature-display')
  expect(display.textContent).toContain('21')
})
