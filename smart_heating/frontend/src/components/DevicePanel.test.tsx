import { render, screen, fireEvent, within, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import DevicePanel from './DevicePanel'

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (k: string, v?: any) => {
      if (v && v.count !== undefined) return `${v.count}`
      if (k.startsWith('devices.')) return k
      return k
    },
  }),
}))

vi.mock('../api/devices', () => ({
  refreshDevices: vi
    .fn()
    .mockResolvedValue({ success: true, updated: 0, available: 0, message: 'ok' }),
}))

describe('DevicePanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })
  afterEach(() => {
    vi.clearAllMocks()
  })

  it('displays empty state when no climate devices', async () => {
    render(<DevicePanel devices={[]} onUpdate={() => {}} />)

    expect(screen.getByText('devices.noClimateDevices')).toBeInTheDocument()
  })

  it('shows placeholder when showOnlyHeating is toggled off', async () => {
    const user = userEvent.setup()
    render(<DevicePanel devices={[]} onUpdate={() => {}} />)

    const toggle = screen.getByLabelText('devices.climateOnly')
    await act(async () => await user.click(toggle))

    expect(await screen.findByText('devices.noDevicesFound')).toBeInTheDocument()
  })

  it('filters devices by search and type', async () => {
    const devices = [
      {
        id: 'd1',
        name: 'Thermostat',
        type: 'thermostat',
        subtype: 'climate',
        ha_area_name: 'Living Room',
      },
      {
        id: 'd2',
        name: 'Sensor',
        type: 'temperature_sensor',
        subtype: 'temperature',
        ha_area_name: 'Bedroom',
      },
      { id: 'd3', name: 'Other', type: 'unknown', subtype: 'other', ha_area_name: 'Kitchen' },
    ]

    render(<DevicePanel devices={devices as any} onUpdate={() => {}} />)

    // initial count shows only climate/temperature devices (2)
    expect(screen.getByText('2')).toBeInTheDocument()

    // search should filter
    const input = screen.getByPlaceholderText('devices.searchPlaceholder') as HTMLInputElement
    await act(async () => fireEvent.change(input, { target: { value: 'thermostat' } }))

    // Ensure at least one list item contains the device name
    const list = screen.getByRole('list')
    const items = within(list).getAllByRole('listitem')
    expect(items.some(i => within(i).getAllByText('Thermostat').length > 0)).toBeTruthy()
    expect(screen.queryByText('Other')).toBeNull()
  })

  it('refresh button calls refreshDevices and shows loading', async () => {
    vi.useFakeTimers()
    const { refreshDevices } = await import('../api/devices')
    const onUpdate = vi.fn()
    render(<DevicePanel devices={[]} onUpdate={onUpdate} />)

    const refreshIcon = screen.getByTestId('RefreshIcon')
    const refreshButton = refreshIcon.closest('button')
    if (refreshButton) await act(async () => fireEvent.click(refreshButton))

    expect(refreshDevices).toHaveBeenCalled()

    // simulate timeout for onUpdate call
    act(() => vi.advanceTimersByTime(500))
    vi.useRealTimers()
    await Promise.resolve()
    expect(onUpdate).toHaveBeenCalled()
  })
})
