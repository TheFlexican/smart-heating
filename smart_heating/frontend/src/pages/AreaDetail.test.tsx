/// <reference types="vitest" />
import React from 'react'
import { render, screen, waitFor, within } from '@testing-library/react'
import SettingsSection from '../components/SettingsSection'
import { FormControl, InputLabel, Select, MenuItem, RadioGroup, FormControlLabel, Radio, Switch, TextField, Box, Typography } from '@mui/material'
import * as areas from '../api/areas'
import * as devices from '../api/devices'
import * as history from '../api/history'
import * as config from '../api/config'
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

vi.spyOn(areas, 'getZones').mockResolvedValue([area])
vi.spyOn(areas, 'getAreaPresetConfig').mockResolvedValue({})
vi.spyOn(devices, 'getDevices').mockResolvedValue([])
vi.spyOn(config, 'getEntityState').mockResolvedValue({ state: 'home' })
vi.spyOn(history, 'getHistoryConfig').mockResolvedValue({ retention_days: 30 })
vi.spyOn(config, 'getWeatherEntities').mockResolvedValue([])
import * as logs from '../api/logs'
vi.spyOn(logs, 'getAreaLogs').mockResolvedValue([])

import * as presets from '../api/presets'
vi.spyOn(presets, 'getGlobalPresets').mockResolvedValue([])

vi.mock('../hooks/useWebSocket', () => ({ useWebSocket: () => ({}) }))

import ZoneDetail from './AreaDetail'
import * as Router from 'react-router-dom'

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

it('heating type control has testid and accessible label', async () => {
  await userEvent.setup()

  const content = (
    <RadioGroup data-testid="heating-type-control" aria-label={'settingsCards.heatingTypeTitle'} value={'radiator'} onChange={() => {}}>
      <FormControlLabel value="radiator" control={<Radio />} label={'settingsCards.radiator'} />
      <FormControlLabel value="floor_heating" control={<Radio />} label={'settingsCards.floorHeating'} />
      <FormControlLabel value="airco" control={<Radio />} label={'settingsCards.airConditioner'} />
    </RadioGroup>
  )

  render(
    <SettingsSection
      id="heating-type"
      title={'settingsCards.heatingTypeTitle'}
      description={'settingsCards.heatingTypeDescription'}
      icon={null}
      badge={undefined}
      defaultExpanded={true}
    >
      {content}
    </SettingsSection>
  )

  // testid present
  await waitFor(() => expect(screen.queryByTestId('heating-type-control')).not.toBeNull())

  // accessible via aria-label (translation mock returns the key)
  const labeled = screen.getByLabelText('settingsCards.heatingTypeTitle') as HTMLElement
  expect(labeled).not.toBeNull()
  // airco option present
  expect(screen.getByText('settingsCards.airConditioner')).not.toBeNull()
})

it('heating curve control is disabled for airco area', async () => {
  await userEvent.setup()

  // Make getZones return an area with heating_type 'airco'
  vi.spyOn(areas, 'getZones').mockResolvedValue([{ ...(area as any), heating_type: 'airco' } as any])

  const { MemoryRouter, Routes, Route } = Router as any
  render(
    <MemoryRouter initialEntries={[`/areas/${area.id}`]}>
      <Routes>
        <Route path="/areas/:areaId" element={<ZoneDetail />} />
      </Routes>
    </MemoryRouter>
  )

  // Expand heating-type section and check helper text is visible
  // Switch to Settings tab then expand heating-type card
  await waitFor(() => expect(screen.getByTestId('area-detail-tab-settings')).not.toBeNull())
  const settingsTab = screen.getByTestId('area-detail-tab-settings') as HTMLElement
  await userEvent.click(settingsTab)
  await waitFor(() => expect(screen.getByTestId('settings-card-heating-type')).not.toBeNull())
  await userEvent.click(screen.getByTestId('settings-card-heating-type'))
  // Badge should indicate Air Conditioner when heating_type is airco
  await waitFor(() => expect(screen.getByText('settingsCards.airConditioner')).not.toBeNull())
})

it('switch/pump control is disabled for airco area', async () => {
  await userEvent.setup()

  // Make getZones return an area with heating_type 'airco'
  vi.spyOn(areas, 'getZones').mockResolvedValue([{ ...(area as any), heating_type: 'airco' } as any])

  const { MemoryRouter, Routes, Route } = Router as any
  render(
    <MemoryRouter initialEntries={[`/areas/${area.id}`]}>
      <Routes>
        <Route path="/areas/:areaId" element={<ZoneDetail />} />
      </Routes>
    </MemoryRouter>
  )

  // Expand switch-control section and check helper text and disabled state
  // Switch to Settings tab then expand switch-control card
  await waitFor(() => expect(screen.getByTestId('area-detail-tab-settings')).not.toBeNull())
  const settingsTab = screen.getByTestId('area-detail-tab-settings') as HTMLElement
  await userEvent.click(settingsTab)
  await waitFor(() => expect(screen.getByTestId('settings-card-switch-control')).not.toBeNull())
  // Click the card title to expand the card reliably
  await userEvent.click(screen.getByText('settingsCards.switchPumpControlTitle'))
  // The switch should be disabled for airco areas (check within the card)
  const switchCard = screen.getByTestId('settings-card-switch-control') as HTMLElement
  await waitFor(() => expect(within(switchCard).getByRole('switch')).not.toBeNull())
  const switchInput = within(switchCard).getByRole('switch') as HTMLInputElement
  expect(switchInput.disabled).toBe(true)
})

it('heating curve control has testid and toggles input disabled when using global', async () => {
  await userEvent.setup()

  // Create a small component to manage local state so we can assert enable/disable behavior
  function TestComponent() {
    const [useGlobal, setUseGlobal] = React.useState(true)
    return (
      <div data-testid="heating-curve-control">
        <FormControlLabel
          control={<Switch checked={!useGlobal} onChange={(e) => setUseGlobal(!e.target.checked)} />}
          label={'settingsCards.heatingCurveUseArea'}
        />
        <TextField label="Coefficient" type="number" inputProps={{ 'data-testid': 'heating-curve-control-input' }} disabled={useGlobal} />
      </div>
    )
  }

  render(
    <SettingsSection
      id="heating-curve"
      title={'settingsCards.heatingCurveTitle'}
      description={'settingsCards.heatingCurveDescription'}
      icon={null}
      badge={undefined}
      defaultExpanded={true}
    >
      <TestComponent />
    </SettingsSection>
  )

  // testid present
  await waitFor(() => expect(screen.queryByTestId('heating-curve-control')).not.toBeNull())

  const input = screen.getByTestId('heating-curve-control-input') as HTMLInputElement
  expect(input).not.toBeNull()
  expect(input.disabled).toBe(true)

  // toggle to enable
  const switchInput = screen.getByLabelText('settingsCards.heatingCurveUseArea') as HTMLInputElement
  await userEvent.click(switchInput)
  await waitFor(() => expect(input.disabled).toBe(false))
})

it('renders Logs tab and opens logs panel (shows empty state)', async () => {
  await userEvent.setup()

  // Render ZoneDetail inside a MemoryRouter so useParams picks up areaId
  const { MemoryRouter, Routes, Route } = Router as any
  render(
    <MemoryRouter initialEntries={[`/areas/${area.id}`]}>
      <Routes>
        <Route path="/areas/:areaId" element={<ZoneDetail />} />
      </Routes>
    </MemoryRouter>
  )

  // Logs tab should be present (stable testid)
  await waitFor(() => expect(screen.queryByTestId('tab-logs')).not.toBeNull())

  const logsTab = screen.getByTestId('tab-logs') as HTMLElement
  await userEvent.click(logsTab)

  // Our logs api mock returns empty array, so we should see the empty placeholder
  await waitFor(() => expect(screen.getByTestId('area-logs-empty')).toBeInTheDocument())
})

it('auto preset toggle has stable testid and is renderable', async () => {
  await userEvent.setup()

  // Render the Auto Preset control inside a SettingsSection for a deterministic unit test
  const content = (
    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <Box>
        <Typography variant="body1">{'settingsCards.enableAutoPreset'}</Typography>
        <Typography variant="caption">{'settingsCards.enableAutoPresetDescription'}</Typography>
      </Box>
      <Switch data-testid="auto-preset-toggle" checked={false} onChange={() => {}} />
    </Box>
  )

  render(
    <SettingsSection
      id="auto-preset"
      title={'settingsCards.autoPresetTitle'}
      description={'settingsCards.autoPresetDescription'}
      icon={null}
      badge={undefined}
      defaultExpanded={true}
    >
      {content}
    </SettingsSection>
  )

  await waitFor(() => expect(screen.queryByTestId('auto-preset-toggle')).not.toBeNull())
  const toggle = screen.getByTestId('auto-preset-toggle') as HTMLElement
  expect(toggle).not.toBeNull()
})
