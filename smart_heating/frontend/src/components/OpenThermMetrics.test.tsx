import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'
import OpenThermMetrics from './OpenThermMetrics'
import * as metricsApi from '../api/metrics'

// Mock the metrics API
vi.mock('../api/metrics', () => ({
  getAdvancedMetrics: vi.fn(),
}))

// Mock recharts to avoid rendering issues in tests
vi.mock('recharts', () => ({
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  Line: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  Legend: () => null,
  ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
  AreaChart: ({ children }: any) => <div data-testid="area-chart">{children}</div>,
  Area: () => null,
}))

describe('OpenThermMetrics', () => {
  const mockMetricsData = {
    metrics: [
      {
        timestamp: '2026-01-01T12:00:00Z',
        outdoor_temp: 5,
        boiler_flow_temp: 55,
        boiler_return_temp: 45,
        boiler_setpoint: 60,
        modulation_level: 75,
        flame_on: true,
      },
      {
        timestamp: '2026-01-01T12:05:00Z',
        outdoor_temp: 4.5,
        boiler_flow_temp: 58,
        boiler_return_temp: 48,
        boiler_setpoint: 62,
        modulation_level: 80,
        flame_on: true,
      },
    ],
  }

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(metricsApi.getAdvancedMetrics).mockResolvedValue(mockMetricsData)
  })

  it('renders loading state initially', () => {
    render(<OpenThermMetrics />)
    expect(screen.getByRole('progressbar')).toBeInTheDocument()
  })

  it('loads and displays metrics data', async () => {
    render(<OpenThermMetrics />)

    await waitFor(() => {
      expect(metricsApi.getAdvancedMetrics).toHaveBeenCalledWith(1, undefined, true, false)
    })

    // Charts are rendered via mocked recharts components
    expect(screen.getByTestId('line-chart')).toBeInTheDocument()
    expect(screen.getByTestId('area-chart')).toBeInTheDocument()
  })

  it('displays statistics cards', async () => {
    render(<OpenThermMetrics />)

    await waitFor(() => {
      expect(screen.getByText(/77.5/)).toBeInTheDocument() // avg modulation number
      expect(screen.getByText(/100.0/)).toBeInTheDocument() // flame on percent number
      expect(screen.getByText(/56.5/)).toBeInTheDocument() // avg flow temp number
      expect(screen.getByText(/46.5/)).toBeInTheDocument() // avg return temp number
      expect(screen.getByText(/10.0/)).toBeInTheDocument() // temp delta number
    })
  })

  it('changes time range when days toggle button is clicked', async () => {
    const user = userEvent.setup()
    render(<OpenThermMetrics />)

    await waitFor(() => {
      expect(screen.getByTestId('line-chart')).toBeInTheDocument()
    })

    const button3d = screen.getByTestId('days-3d')
    const initialCallCount = vi.mocked(metricsApi.getAdvancedMetrics).mock.calls.length
    await user.click(button3d)

    await waitFor(() => {
      expect(vi.mocked(metricsApi.getAdvancedMetrics).mock.calls.length).toBeGreaterThan(
        initialCallCount,
      )
      // Last call should be with 3 days
      const lastCall = vi.mocked(metricsApi.getAdvancedMetrics).mock.calls[
        vi.mocked(metricsApi.getAdvancedMetrics).mock.calls.length - 1
      ]
      expect(lastCall).toEqual([3, undefined, true, false])
    })
  })

  it('changes time range when hours toggle button is clicked', async () => {
    const user = userEvent.setup()
    render(<OpenThermMetrics />)

    await waitFor(() => {
      expect(screen.getByTestId('line-chart')).toBeInTheDocument()
    })

    const button2h = screen.getByTestId('hours-2h')
    const initialCallCount = vi.mocked(metricsApi.getAdvancedMetrics).mock.calls.length
    await user.click(button2h)

    await waitFor(() => {
      expect(vi.mocked(metricsApi.getAdvancedMetrics).mock.calls.length).toBeGreaterThan(
        initialCallCount,
      )
      // Last call should be with 2 hours
      const lastCall = vi.mocked(metricsApi.getAdvancedMetrics).mock.calls[
        vi.mocked(metricsApi.getAdvancedMetrics).mock.calls.length - 1
      ]
      expect(lastCall).toEqual([2, undefined, false, true])
    })
  })

  it('switches between hours and days correctly', async () => {
    const user = userEvent.setup()
    render(<OpenThermMetrics />)

    await waitFor(() => {
      expect(screen.getByTestId('line-chart')).toBeInTheDocument()
    })

    // Initially on 1d
    expect(vi.mocked(metricsApi.getAdvancedMetrics)).toHaveBeenCalledWith(1, undefined, true, false)

    // Switch to 5h
    const button5h = screen.getByTestId('hours-5h')
    await user.click(button5h)

    await waitFor(() => {
      const lastCall = vi.mocked(metricsApi.getAdvancedMetrics).mock.calls[
        vi.mocked(metricsApi.getAdvancedMetrics).mock.calls.length - 1
      ]
      expect(lastCall).toEqual([5, undefined, false, true])
    })

    // Switch back to 5d
    const button5d = screen.getByTestId('days-5d')
    await user.click(button5d)

    await waitFor(() => {
      const lastCall = vi.mocked(metricsApi.getAdvancedMetrics).mock.calls[
        vi.mocked(metricsApi.getAdvancedMetrics).mock.calls.length - 1
      ]
      expect(lastCall).toEqual([5, undefined, true, false])
    })
  })

  it('toggles auto-refresh when switch is clicked', async () => {
    const user = userEvent.setup()
    render(<OpenThermMetrics />)

    await waitFor(() => {
      expect(screen.getByTestId('line-chart')).toBeInTheDocument()
    })

    const autoRefreshSwitch = screen.getByRole('switch')
    expect(autoRefreshSwitch).toBeChecked()

    await user.click(autoRefreshSwitch)
    expect(autoRefreshSwitch).not.toBeChecked()
  })

  it('displays error message when API fails', async () => {
    vi.mocked(metricsApi.getAdvancedMetrics).mockRejectedValue(new Error('API Error'))

    render(<OpenThermMetrics />)
    // The component renders an Alert when the API fails; assert alert exists
    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
    })
  })

  it('handles empty metrics data gracefully', async () => {
    vi.mocked(metricsApi.getAdvancedMetrics).mockResolvedValue({ metrics: [] })

    render(<OpenThermMetrics />)
    await waitFor(() => {
      // Multiple stat cards may show 0 values; assert at least one exists
      const zeroPercents = screen.getAllByText(/0%/)
      expect(zeroPercents.length).toBeGreaterThanOrEqual(1)

      const zeroTemps = screen.getAllByText(/0°C/)
      expect(zeroTemps.length).toBeGreaterThanOrEqual(1)
    })
  })
})
