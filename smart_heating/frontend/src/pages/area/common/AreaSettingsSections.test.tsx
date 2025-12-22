import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import buildAreaSettingsSections from '../AreaSettingsSections'
import DraggableSettings from '../../../../components/common/DraggableSettings'

vi.mock('../../../../api/areas', () => ({
  setAreaAutoPreset: vi.fn().mockResolvedValue(undefined),
  setSwitchShutdown: vi.fn().mockResolvedValue(undefined),
  setHvacMode: vi.fn().mockResolvedValue(undefined),
  setAreaPresetConfig: vi.fn().mockResolvedValue(undefined),
  setAreaHeatingCurve: vi.fn().mockResolvedValue(undefined),
  callService: vi.fn().mockResolvedValue(undefined),
}))

vi.mock('../../../../api/sensors', () => ({
  setAreaPresenceConfig: vi.fn().mockResolvedValue(undefined),
}))

// Mock child components to keep tests focused
vi.mock('../../../../components/common/PresetControls', () => ({
  __esModule: true,
  default: (props: any) => <div data-testid="preset-controls">PresetControls</div>,
}))
vi.mock('../../../../components/global/AutoPresetControls', () => ({
  __esModule: true,
  default: (props: any) => <div data-testid="auto-preset-controls">AutoPresetControls</div>,
}))
vi.mock('../../../../components/area/SensorConfigControls', () => ({
  __esModule: true,
  default: (props: any) => <div data-testid="sensor-config-controls">SensorConfigControls</div>,
}))
vi.mock('../../../../components/area/OutdoorSensorControls', () => ({
  __esModule: true,
  default: (props: any) => <div data-testid="outdoor-controls">OutdoorSensorControls</div>,
}))
vi.mock('../../../../components/common/StorageBackendInfo', () => ({
  __esModule: true,
  default: (props: any) => <div data-testid="storage-info">StorageBackendInfo</div>,
}))
vi.mock('../../../../components/area/HistoryMigrationControls', () => ({
  __esModule: true,
  default: (props: any) => <div data-testid="history-migration">HistoryMigrationControls</div>,
}))

const defaultT = (k: string) => k

const baseArea = {
  id: 'area1',
  name: 'Test Area',
  enabled: true,
  heating_type: 'radiator',
  preset_mode: 'comfort',
  shutdown_switches_when_idle: true,
  window_sensors: [],
  auto_preset_enabled: false,
  night_boost_enabled: false,
  smart_boost_enabled: false,
}

describe('AreaSettingsSections', () => {
  it('renders heating-type and preset sections', () => {
    const sections = buildAreaSettingsSections({
      t: defaultT,
      area: baseArea as any,
      globalPresets: {
        away_temp: 16,
        eco_temp: 18,
        comfort_temp: 21,
        home_temp: 20,
        sleep_temp: 17,
        activity_temp: 22,
      } as any,
      getPresetTemp: () => '20°C',
      loadData: async () => {},
      entityStates: {},
      historyRetention: 30,
      setHistoryRetention: () => {},
      storageBackend: 'json',
      databaseStats: {},
      migrating: false,
      setMigrating: () => {},
      recordInterval: 60,
      loadHistoryConfig: async () => {},
      useGlobalHeatingCurve: true,
      setUseGlobalHeatingCurve: () => {},
      areaHeatingCurveCoefficient: null,
      setAreaHeatingCurveCoefficient: () => {},
    })

    render(<DraggableSettings sections={sections as any} storageKey="test" />)

    expect(screen.getByTestId('settings-card-heating-type')).toBeInTheDocument()
    expect(screen.getByTestId('settings-card-preset-modes')).toBeInTheDocument()
  })

  it('disables switch input for airco area', () => {
    const aircoArea = { ...baseArea, heating_type: 'airco' }
    const sections = buildAreaSettingsSections({
      t: defaultT,
      area: aircoArea as any,
      globalPresets: null,
      getPresetTemp: () => '20°C',
      loadData: async () => {},
      entityStates: {},
      historyRetention: 30,
      setHistoryRetention: () => {},
      storageBackend: 'json',
      databaseStats: {},
      migrating: false,
      setMigrating: () => {},
      recordInterval: 60,
      loadHistoryConfig: async () => {},
      useGlobalHeatingCurve: true,
      setUseGlobalHeatingCurve: () => {},
      areaHeatingCurveCoefficient: null,
      setAreaHeatingCurveCoefficient: () => {},
    })

    const sw = sections.find(s => s.id === 'switch-control')!
    render(<div>{sw.content}</div>)

    const input = screen.getByRole('switch') as HTMLInputElement
    expect(input.disabled).toBeTruthy()
  })

  it('calls setAreaAutoPreset when toggling auto preset', async () => {
    const user = userEvent.setup()
    const areas = await import('../../../../api/areas')
    const sections = buildAreaSettingsSections({
      t: defaultT,
      area: baseArea as any,
      globalPresets: null,
      getPresetTemp: () => '20°C',
      loadData: async () => {},
      entityStates: {},
      historyRetention: 30,
      setHistoryRetention: () => {},
      storageBackend: 'json',
      databaseStats: {},
      migrating: false,
      setMigrating: () => {},
      recordInterval: 60,
      loadHistoryConfig: async () => {},
      useGlobalHeatingCurve: true,
      setUseGlobalHeatingCurve: () => {},
      areaHeatingCurveCoefficient: null,
      setAreaHeatingCurveCoefficient: () => {},
    })

    const ap = sections.find(s => s.id === 'auto-preset')!
    render(<div>{ap.content}</div>)

    const toggle = screen.getByRole('switch')
    await user.click(toggle)

    expect(areas.setAreaAutoPreset).toHaveBeenCalled()
  })
})
