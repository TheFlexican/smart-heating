/// <reference types="vitest" />
import { render, screen } from '@testing-library/react'
import { vi, it, describe, expect } from 'vitest'
import ZoneCard from './ZoneCard'

// Mock react-i18next to provide a basic translation function
vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string, v?: any) => {
  if (v && v.temp) return `${v.temp}°C`
  if (k.startsWith('presets.')) return k.split('.')[1].toUpperCase()
  return k
} }) }))

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
  current_temperature: 19.2
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
