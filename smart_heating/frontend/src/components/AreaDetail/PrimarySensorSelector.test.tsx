import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import { PrimarySensorSelector } from './PrimarySensorSelector'
import { Zone } from '../../types'

// Mock translation
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}))

describe('PrimarySensorSelector', () => {
  const mockArea: Zone = {
    id: 'living_room',
    name: 'Living Room',
    state: 'heating',
    enabled: true,
    target_temperature: 21.0,
    primary_temperature_sensor: null,
    devices: [
      {
        id: 'sensor1',
        name: 'Temperature Sensor 1',
        type: 'temperature_sensor',
        entity_id: 'sensor.temp1',
      },
      {
        id: 'thermostat1',
        name: 'Thermostat',
        type: 'thermostat',
        entity_id: 'climate.living',
      },
    ],
  } as Zone

  const mockOnPrimarySensorChange = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders without crashing', () => {
    render(
      <PrimarySensorSelector area={mockArea} onPrimarySensorChange={mockOnPrimarySensorChange} />,
    )
    expect(screen.getByText('areaDetail.primaryTemperatureSensor')).toBeInTheDocument()
  })

  it('displays auto option by default when no sensor is selected', () => {
    render(
      <PrimarySensorSelector area={mockArea} onPrimarySensorChange={mockOnPrimarySensorChange} />,
    )
    const select = screen.getByRole('combobox')
    expect(select).toHaveTextContent('areaDetail.autoAllSensors')
  })

  it('displays selected sensor when one is set', () => {
    const areaWithSensor = { ...mockArea, primary_temperature_sensor: 'sensor.temp1' }
    render(
      <PrimarySensorSelector
        area={areaWithSensor}
        onPrimarySensorChange={mockOnPrimarySensorChange}
      />,
    )
    // The select value should be sensor.temp1
    const select = screen.getByRole('combobox')
    expect(select).toBeInTheDocument()
  })

  it('lists temperature sensors and thermostats', () => {
    render(
      <PrimarySensorSelector area={mockArea} onPrimarySensorChange={mockOnPrimarySensorChange} />,
    )
    const select = screen.getByRole('combobox')
    fireEvent.mouseDown(select)

    // Should show auto option and both devices
    expect(screen.getAllByText('areaDetail.autoAllSensors').length).toBeGreaterThan(0)
    expect(screen.getByText(/Temperature Sensor 1/)).toBeInTheDocument()
    expect(screen.getByText(/Thermostat/)).toBeInTheDocument()
  })

  it('calls onPrimarySensorChange with null when auto is selected', async () => {
    mockOnPrimarySensorChange.mockResolvedValue(undefined)
    const areaWithSensor = { ...mockArea, primary_temperature_sensor: 'sensor.temp1' }
    render(
      <PrimarySensorSelector
        area={areaWithSensor}
        onPrimarySensorChange={mockOnPrimarySensorChange}
      />,
    )

    const select = screen.getByRole('combobox')
    fireEvent.mouseDown(select)
    const autoOption = screen.getByText('areaDetail.autoAllSensors')
    fireEvent.click(autoOption)

    await waitFor(() => {
      expect(mockOnPrimarySensorChange).toHaveBeenCalledWith(null)
    })
  })

  it('calls onPrimarySensorChange with sensor id when sensor is selected', async () => {
    mockOnPrimarySensorChange.mockResolvedValue(undefined)
    render(
      <PrimarySensorSelector area={mockArea} onPrimarySensorChange={mockOnPrimarySensorChange} />,
    )

    const select = screen.getByRole('combobox')
    fireEvent.mouseDown(select)
    const sensorOption = screen.getByText(/Temperature Sensor 1/)
    fireEvent.click(sensorOption)

    await waitFor(() => {
      expect(mockOnPrimarySensorChange).toHaveBeenCalledWith('sensor.temp1')
    })
  })
})
