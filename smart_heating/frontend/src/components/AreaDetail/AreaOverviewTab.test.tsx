import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import { AreaOverviewTab } from './AreaOverviewTab'
import { Zone } from '../../types'

// Mock translation
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, options?: any) => {
      if (key === 'areaDetail.devicesAssigned') {
        return `${options?.count} devices`
      }
      if (key === 'areaDetail.presetModeActive') {
        return `Preset mode: ${options?.mode}`
      }
      return key
    },
  }),
}))

describe('AreaOverviewTab', () => {
  const mockArea: Zone = {
    id: 'living_room',
    name: 'Living Room',
    state: 'heating',
    enabled: true,
    target_temperature: 21.0,
    current_temperature: 20.5,
    preset_mode: 'none',
    devices: [
      { id: 'device1', name: 'Thermostat', type: 'thermostat', entity_id: 'climate.living_room' },
      {
        id: 'device2',
        name: 'Temperature Sensor',
        type: 'temperature_sensor',
        entity_id: 'sensor.temp',
      },
    ],
    trv_entities: [
      { entity_id: 'climate.trv1', role: 'both', name: 'TRV 1' },
      { entity_id: 'climate.trv2', role: 'position', name: 'TRV 2' },
    ],
    trvs: [
      { entity_id: 'climate.trv1', name: 'TRV 1', open: true, position: 75 },
      { entity_id: 'climate.trv2', name: 'TRV 2', open: false, position: 25 },
    ],
  } as Zone

  const mockHandlers = {
    onTemperatureChange: vi.fn(),
    onTemperatureCommit: vi.fn(),
    onTrvDialogOpen: vi.fn(),
    onStartEditingTrv: vi.fn(),
    onEditingTrvNameChange: vi.fn(),
    onEditingTrvRoleChange: vi.fn(),
    onSaveTrv: vi.fn(),
    onCancelEditingTrv: vi.fn(),
    onDeleteTrv: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders without crashing', () => {
    render(
      <AreaOverviewTab
        area={mockArea}
        temperature={21}
        enabled={true}
        editingTrvId={null}
        editingTrvName={null}
        editingTrvRole={null}
        {...mockHandlers}
      />,
    )
    expect(screen.getByText('areaDetail.temperatureControl')).toBeInTheDocument()
  })

  it('displays target temperature', () => {
    render(
      <AreaOverviewTab
        area={mockArea}
        temperature={21}
        enabled={true}
        editingTrvId={null}
        editingTrvName={null}
        editingTrvRole={null}
        {...mockHandlers}
      />,
    )
    expect(screen.getByTestId('target-temperature-display')).toHaveTextContent('21°C')
  })

  it('displays current temperature when available', () => {
    render(
      <AreaOverviewTab
        area={mockArea}
        temperature={21}
        enabled={true}
        editingTrvId={null}
        editingTrvName={null}
        editingTrvRole={null}
        {...mockHandlers}
      />,
    )
    expect(screen.getByText('20.5°C')).toBeInTheDocument()
  })

  it('disables temperature slider when area is disabled', () => {
    render(
      <AreaOverviewTab
        area={mockArea}
        temperature={21}
        enabled={false}
        editingTrvId={null}
        editingTrvName={null}
        editingTrvRole={null}
        {...mockHandlers}
      />,
    )
    const slider = screen.getByRole('slider')
    expect(slider).toBeDisabled()
  })

  it('disables temperature slider when preset mode is active', () => {
    const areaWithPreset = { ...mockArea, preset_mode: 'comfort' }
    render(
      <AreaOverviewTab
        area={areaWithPreset}
        temperature={21}
        enabled={true}
        editingTrvId={null}
        editingTrvName={null}
        editingTrvRole={null}
        {...mockHandlers}
      />,
    )
    const slider = screen.getByRole('slider')
    expect(slider).toBeDisabled()
  })

  it('displays preset mode indicator when active', () => {
    const areaWithPreset = { ...mockArea, preset_mode: 'comfort', state: 'heating' }
    render(
      <AreaOverviewTab
        area={areaWithPreset}
        temperature={21}
        enabled={true}
        editingTrvId={null}
        editingTrvName={null}
        editingTrvRole={null}
        {...mockHandlers}
      />,
    )
    expect(screen.getByText(/Preset mode:/)).toBeInTheDocument()
  })

  it('displays TRV list when TRVs are configured', () => {
    render(
      <AreaOverviewTab
        area={mockArea}
        temperature={21}
        enabled={true}
        editingTrvId={null}
        editingTrvName={null}
        editingTrvRole={null}
        {...mockHandlers}
      />,
    )
    expect(screen.getByText('TRV 1')).toBeInTheDocument()
    expect(screen.getByText('TRV 2')).toBeInTheDocument()
  })

  it('calls onTrvDialogOpen when Add TRV button is clicked', () => {
    render(
      <AreaOverviewTab
        area={mockArea}
        temperature={21}
        enabled={true}
        editingTrvId={null}
        editingTrvName={null}
        editingTrvRole={null}
        {...mockHandlers}
      />,
    )
    const addButton = screen.getByTestId('trv-add-button-overview')
    fireEvent.click(addButton)
    expect(mockHandlers.onTrvDialogOpen).toHaveBeenCalledTimes(1)
  })

  it('displays quick stats correctly', () => {
    render(
      <AreaOverviewTab
        area={mockArea}
        temperature={21}
        enabled={true}
        editingTrvId={null}
        editingTrvName={null}
        editingTrvRole={null}
        {...mockHandlers}
      />,
    )
    expect(screen.getByText('2 devices')).toBeInTheDocument()
    expect(screen.getByText('heating')).toBeInTheDocument()
    expect(screen.getByText('living_room')).toBeInTheDocument()
  })

  it('shows TRV open/closed status', () => {
    render(
      <AreaOverviewTab
        area={mockArea}
        temperature={21}
        enabled={true}
        editingTrvId={null}
        editingTrvName={null}
        editingTrvRole={null}
        {...mockHandlers}
      />,
    )
    expect(screen.getByTestId('trv-open-climate.trv1')).toBeInTheDocument()
    expect(screen.getByTestId('trv-open-climate.trv2')).toBeInTheDocument()
  })

  it('shows TRV position percentage', () => {
    render(
      <AreaOverviewTab
        area={mockArea}
        temperature={21}
        enabled={true}
        editingTrvId={null}
        editingTrvName={null}
        editingTrvRole={null}
        {...mockHandlers}
      />,
    )
    expect(screen.getByTestId('trv-position-climate.trv1')).toHaveTextContent('75%')
    expect(screen.getByTestId('trv-position-climate.trv2')).toHaveTextContent('25%')
  })

  it('shows no TRV message when no TRVs configured', () => {
    const areaWithoutTrvs = { ...mockArea, trv_entities: [] }
    render(
      <AreaOverviewTab
        area={areaWithoutTrvs}
        temperature={21}
        enabled={true}
        editingTrvId={null}
        editingTrvName={null}
        editingTrvRole={null}
        {...mockHandlers}
      />,
    )
    expect(
      screen.getByText('No TRVs configured for this area. Click Add TRV to add one.'),
    ).toBeInTheDocument()
  })

  it('does not show current temperature section when undefined', () => {
    const areaWithoutTemp = { ...mockArea, current_temperature: undefined }
    render(
      <AreaOverviewTab
        area={areaWithoutTemp}
        temperature={21}
        enabled={true}
        editingTrvId={null}
        editingTrvName={null}
        editingTrvRole={null}
        {...mockHandlers}
      />,
    )
    expect(screen.queryByText('areaDetail.currentTemperature')).not.toBeInTheDocument()
  })
})
