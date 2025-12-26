import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import { AvailableDevicesList } from './AvailableDevicesList'
import { Zone, Device } from '../../types'

// Mock translation
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, options?: any) => {
      if (key === 'areaDetail.availableDevices') return `${options?.count} available`
      if (key === 'areaDetail.availableDevicesDescription') return `Devices for ${options?.area}`
      return key
    },
  }),
}))

describe('AvailableDevicesList', () => {
  const mockArea: Zone = {
    id: 'living_room',
    name: 'Living Room',
    state: 'heating',
    enabled: true,
    target_temperature: 21.0,
    devices: [],
  } as Zone

  const mockAvailableDevices: Device[] = [
    {
      id: 'sensor1',
      name: 'Temperature Sensor',
      type: 'temperature_sensor',
      entity_id: 'sensor.temp',
      subtype: 'temperature',
    } as Device,
    {
      id: 'climate1',
      name: 'Climate Device',
      type: 'thermostat',
      entity_id: 'climate.hvac',
      subtype: 'climate',
    } as Device,
    {
      id: 'switch1',
      name: 'Switch Device',
      type: 'switch',
      entity_id: 'switch.heating',
    } as Device,
  ]

  const mockHandlers = {
    onShowOnlyHeatingChange: vi.fn(),
    onDeviceSearchChange: vi.fn(),
    onAddDevice: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders without crashing', () => {
    render(
      <AvailableDevicesList
        area={mockArea}
        availableDevices={mockAvailableDevices}
        showOnlyHeating={true}
        deviceSearch=""
        {...mockHandlers}
      />,
    )
    expect(screen.getByText(/available/)).toBeInTheDocument()
  })

  it('filters devices by heating type when showOnlyHeating is true', () => {
    render(
      <AvailableDevicesList
        area={mockArea}
        availableDevices={mockAvailableDevices}
        showOnlyHeating={true}
        deviceSearch=""
        {...mockHandlers}
      />,
    )
    // Should show only climate and temperature devices
    expect(screen.getByText('Temperature Sensor')).toBeInTheDocument()
    expect(screen.getByText('Climate Device')).toBeInTheDocument()
    expect(screen.queryByText('Switch Device')).not.toBeInTheDocument()
  })

  it('shows all devices when showOnlyHeating is false', () => {
    render(
      <AvailableDevicesList
        area={mockArea}
        availableDevices={mockAvailableDevices}
        showOnlyHeating={false}
        deviceSearch=""
        {...mockHandlers}
      />,
    )
    expect(screen.getByText('Temperature Sensor')).toBeInTheDocument()
    expect(screen.getByText('Climate Device')).toBeInTheDocument()
    expect(screen.getByText('Switch Device')).toBeInTheDocument()
  })

  it('filters devices by search term', () => {
    render(
      <AvailableDevicesList
        area={mockArea}
        availableDevices={mockAvailableDevices}
        showOnlyHeating={false}
        deviceSearch="climate"
        {...mockHandlers}
      />,
    )
    expect(screen.getByText('Climate Device')).toBeInTheDocument()
    expect(screen.queryByText('Temperature Sensor')).not.toBeInTheDocument()
    expect(screen.queryByText('Switch Device')).not.toBeInTheDocument()
  })

  it('calls onShowOnlyHeatingChange when toggle is clicked', () => {
    render(
      <AvailableDevicesList
        area={mockArea}
        availableDevices={mockAvailableDevices}
        showOnlyHeating={true}
        deviceSearch=""
        {...mockHandlers}
      />,
    )
    const toggle = screen.getByRole('switch')
    fireEvent.click(toggle)
    expect(mockHandlers.onShowOnlyHeatingChange).toHaveBeenCalledWith(false)
  })

  it('calls onDeviceSearchChange when search input changes', async () => {
    const user = userEvent.setup()
    render(
      <AvailableDevicesList
        area={mockArea}
        availableDevices={mockAvailableDevices}
        showOnlyHeating={false}
        deviceSearch=""
        {...mockHandlers}
      />,
    )
    const searchInput = screen.getByPlaceholderText('areaDetail.searchPlaceholder')
    await user.type(searchInput, 'test')
    expect(mockHandlers.onDeviceSearchChange).toHaveBeenCalled()
  })

  it('calls onAddDevice when add button is clicked', () => {
    mockHandlers.onAddDevice.mockResolvedValue(undefined)
    render(
      <AvailableDevicesList
        area={mockArea}
        availableDevices={mockAvailableDevices}
        showOnlyHeating={false}
        deviceSearch=""
        {...mockHandlers}
      />,
    )
    const addButton = screen.getByTestId('add-available-device-sensor.temp')
    fireEvent.click(addButton)
    expect(mockHandlers.onAddDevice).toHaveBeenCalledWith(mockAvailableDevices[0])
  })

  it('disables add button for valves in airco areas', () => {
    const aircoArea = { ...mockArea, heating_type: 'airco' }
    const devicesWithValve: Device[] = [
      {
        id: 'valve1',
        name: 'Valve',
        type: 'valve',
        entity_id: 'valve.heating',
      } as Device,
    ]

    render(
      <AvailableDevicesList
        area={aircoArea}
        availableDevices={devicesWithValve}
        showOnlyHeating={false}
        deviceSearch=""
        {...mockHandlers}
      />,
    )
    const addButton = screen.getByTestId('add-available-device-valve.heating')
    expect(addButton).toBeDisabled()
  })

  it('shows info message when no devices match search', () => {
    render(
      <AvailableDevicesList
        area={mockArea}
        availableDevices={mockAvailableDevices}
        showOnlyHeating={false}
        deviceSearch="nonexistent"
        {...mockHandlers}
      />,
    )
    expect(screen.getByText('areaDetail.noDevicesMatch')).toBeInTheDocument()
  })

  it('shows info message when no climate devices available', () => {
    const nonClimateDevices: Device[] = [
      {
        id: 'switch1',
        name: 'Switch',
        type: 'switch',
        entity_id: 'switch.heating',
      } as Device,
    ]

    render(
      <AvailableDevicesList
        area={mockArea}
        availableDevices={nonClimateDevices}
        showOnlyHeating={true}
        deviceSearch=""
        {...mockHandlers}
      />,
    )
    expect(screen.getByText('areaDetail.noClimateDevices')).toBeInTheDocument()
  })

  it('displays device types and subtypes', () => {
    render(
      <AvailableDevicesList
        area={mockArea}
        availableDevices={mockAvailableDevices}
        showOnlyHeating={false}
        deviceSearch=""
        {...mockHandlers}
      />,
    )
    expect(screen.getByText('temperature sensor')).toBeInTheDocument()
    expect(screen.getByText('temperature')).toBeInTheDocument()
    expect(screen.getByText('climate')).toBeInTheDocument()
  })
})
