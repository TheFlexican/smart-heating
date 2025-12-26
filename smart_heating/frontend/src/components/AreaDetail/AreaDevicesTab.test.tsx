import { render, screen } from '@testing-library/react'
import { vi } from 'vitest'
import { AreaDevicesTab } from './AreaDevicesTab'
import { Zone, Device } from '../../types'

// Mock translation
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, options?: any) => {
      if (key === 'areaDetail.assignedDevices') return `${options?.count} devices`
      if (key === 'areaDetail.availableDevices') return `${options?.count} available`
      return key
    },
  }),
}))

describe('AreaDevicesTab', () => {
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
        entity_id: 'climate.living_room',
        current_temperature: 20.5,
      },
    ],
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
      id: 'valve1',
      name: 'Valve',
      type: 'valve',
      entity_id: 'valve.heating',
      subtype: 'climate',
    } as Device,
  ]

  const mockHandlers = {
    onPrimarySensorChange: vi.fn(),
    onRemoveDevice: vi.fn(),
    onAddDevice: vi.fn(),
    getDeviceStatusIcon: vi.fn(() => <div>Icon</div>),
    getDeviceStatus: vi.fn(() => '20.5°C'),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders without crashing', () => {
    render(
      <AreaDevicesTab area={mockArea} availableDevices={mockAvailableDevices} {...mockHandlers} />,
    )
    expect(screen.getByText('areaDetail.primaryTemperatureSensor')).toBeInTheDocument()
  })

  it('renders all three sub-sections', () => {
    render(
      <AreaDevicesTab area={mockArea} availableDevices={mockAvailableDevices} {...mockHandlers} />,
    )
    // Primary sensor selector
    expect(screen.getByText('areaDetail.primaryTemperatureSensor')).toBeInTheDocument()
    // Assigned devices
    expect(screen.getByText('1 devices')).toBeInTheDocument()
    // Available devices
    expect(screen.getByText('2 available')).toBeInTheDocument()
  })

  it('displays assigned device correctly', () => {
    render(
      <AreaDevicesTab area={mockArea} availableDevices={mockAvailableDevices} {...mockHandlers} />,
    )
    expect(screen.getByText('Thermostat')).toBeInTheDocument()
  })

  it('displays available devices correctly', () => {
    render(
      <AreaDevicesTab area={mockArea} availableDevices={mockAvailableDevices} {...mockHandlers} />,
    )
    expect(screen.getByText('Temperature Sensor')).toBeInTheDocument()
    expect(screen.getByText('Valve')).toBeInTheDocument()
  })
})
