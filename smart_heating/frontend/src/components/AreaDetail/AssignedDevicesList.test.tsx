import { render, screen, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
import { AssignedDevicesList } from './AssignedDevicesList'
import { Zone } from '../../types'

// Mock translation
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, options?: any) => {
      if (key === 'areaDetail.assignedDevices') return `${options?.count} devices`
      return key
    },
  }),
}))

describe('AssignedDevicesList', () => {
  const mockArea: Zone = {
    id: 'living_room',
    name: 'Living Room',
    state: 'heating',
    enabled: true,
    target_temperature: 21.0,
    devices: [
      {
        id: 'device1',
        name: 'Thermostat',
        type: 'thermostat',
        entity_id: 'climate.living',
        current_temperature: 20.5,
      },
      {
        id: 'device2',
        name: 'Temperature Sensor',
        type: 'temperature_sensor',
        entity_id: 'sensor.temp',
        temperature: 20.3,
      },
    ],
  } as Zone

  const mockHandlers = {
    onRemoveDevice: vi.fn(),
    getDeviceStatusIcon: vi.fn(() => <div>Icon</div>),
    getDeviceStatus: vi.fn(device => {
      if (device.type === 'thermostat') return '20.5°C → 21.0°C'
      return '20.3°C'
    }),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders without crashing', () => {
    render(<AssignedDevicesList area={mockArea} {...mockHandlers} />)
    expect(screen.getByText('2 devices')).toBeInTheDocument()
  })

  it('displays all assigned devices', () => {
    render(<AssignedDevicesList area={mockArea} {...mockHandlers} />)
    expect(screen.getByText('Thermostat')).toBeInTheDocument()
    expect(screen.getByText('Temperature Sensor')).toBeInTheDocument()
  })

  it('displays device status from getDeviceStatus', () => {
    render(<AssignedDevicesList area={mockArea} {...mockHandlers} />)
    expect(screen.getByText('20.5°C → 21.0°C')).toBeInTheDocument()
    expect(screen.getByText('20.3°C')).toBeInTheDocument()
  })

  it('shows heating chip when thermostat is heating', () => {
    render(<AssignedDevicesList area={mockArea} {...mockHandlers} />)
    expect(screen.getByTestId('device-heating-chip-device1')).toBeInTheDocument()
  })

  it('does not show heating chip when not heating', () => {
    const areaNotHeating = {
      ...mockArea,
      target_temperature: 19.0, // Lower than current
    }
    render(<AssignedDevicesList area={areaNotHeating} {...mockHandlers} />)
    expect(screen.queryByTestId('device-heating-chip-device1')).not.toBeInTheDocument()
  })

  it('calls onRemoveDevice when remove button is clicked', () => {
    mockHandlers.onRemoveDevice.mockResolvedValue(undefined)
    render(<AssignedDevicesList area={mockArea} {...mockHandlers} />)

    const removeButton = screen.getByTestId('remove-device-climate.living')
    fireEvent.click(removeButton)

    expect(mockHandlers.onRemoveDevice).toHaveBeenCalledWith('climate.living')
  })

  it('shows info message when no devices assigned', () => {
    const areaWithoutDevices = { ...mockArea, devices: [] }
    render(<AssignedDevicesList area={areaWithoutDevices} {...mockHandlers} />)
    expect(screen.getByText('areaDetail.noDevicesAssigned')).toBeInTheDocument()
  })

  it('shows disabled for airco message for valves in airco areas', () => {
    const areaWithValve: Zone = {
      ...mockArea,
      heating_type: 'airco',
      devices: [
        {
          id: 'valve1',
          name: 'Valve',
          type: 'valve',
          entity_id: 'valve.heating',
          position: 50,
        },
      ],
    } as Zone

    render(<AssignedDevicesList area={areaWithValve} {...mockHandlers} />)
    expect(screen.getByTestId('device-disabled-airco-valve1')).toBeInTheDocument()
  })

  it('displays device types correctly', () => {
    render(<AssignedDevicesList area={mockArea} {...mockHandlers} />)
    expect(screen.getByText('thermostat')).toBeInTheDocument()
    expect(screen.getByText('temperature sensor')).toBeInTheDocument()
  })
})
