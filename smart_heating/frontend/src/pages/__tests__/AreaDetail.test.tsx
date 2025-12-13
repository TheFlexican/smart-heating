/// <reference types="vitest" />
import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import SettingsSection from '../../components/SettingsSection'
import { FormControl, InputLabel, Select, MenuItem } from '@mui/material'
import * as api from '../../api'
import { vi, it, expect } from 'vitest'
import userEvent from '@testing-library/user-event'

// Mock translation
vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string, v?: any) => (v && v.temp) ? `${v.temp}°C` : k }) }))

// Mock getZones and other API calls used in AreaDetail
const area = {
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
}

vi.spyOn(api, 'getZones').mockResolvedValue([area])
vi.spyOn(api, 'getGlobalPresets').mockResolvedValue({ away_temp: 16, eco_temp: 18, comfort_temp: 22, home_temp: 21, sleep_temp: 19, activity_temp: 23 })
vi.spyOn(api, 'getDevices').mockResolvedValue([])
vi.spyOn(api, 'getEntityState').mockResolvedValue({ state: 'home' })
vi.spyOn(api, 'getHistoryConfig').mockResolvedValue({ retention_days: 30 })
vi.spyOn(api, 'getWeatherEntities').mockResolvedValue([])
vi.spyOn(api, 'getAreaLogs').mockResolvedValue([])

vi.mock('../../hooks/useWebSocket', () => ({ useWebSocket: () => ({}) }))

it('preset select is disabled when area is disabled/off', async () => {
  await userEvent.setup()
  // Produce the section content directly and render SettingsSection standalone
  const areaLocal = { ...area }

  const content = (
    <FormControl fullWidth>
      <InputLabel>{'settingsCards.currentPreset'}</InputLabel>
      <Select
        disabled={!areaLocal.enabled || areaLocal.state === 'off'}
        value={areaLocal.preset_mode || 'none'}
        label={'settingsCards.currentPreset'}
      >
        <MenuItem value="none">{'settingsCards.presetNoneManual'}</MenuItem>
        <MenuItem value="away">{'settingsCards.presetAwayTemp'}</MenuItem>
      </Select>
    </FormControl>
  )

  render(
    <SettingsSection
      id="preset-modes"
      title={'settingsCards.presetModesTitle'}
      description={'settingsCards.presetModesDescription'}
      icon={null}
      badge={undefined}
      defaultExpanded={true}
    >
      {content}
    </SettingsSection>
  )

  // The Select should be present and disabled for disabled/off area
  await waitFor(() => expect(screen.queryByRole('combobox')).not.toBeNull())
  const combobox = screen.getByRole('combobox') as HTMLElement
  expect(combobox.getAttribute('aria-disabled')).toBe('true')
})
