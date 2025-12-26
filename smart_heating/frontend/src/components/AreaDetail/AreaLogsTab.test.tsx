import { render, screen, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
import { AreaLogsTab } from './AreaLogsTab'
import { AreaLogEntry } from '../../api/logs'

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        'areaDetail.heatingStrategyLogs': 'Heating Strategy Logs',
        'areaDetail.refresh': 'Refresh',
        'areaDetail.logsDescription': 'View heating strategy logs',
        'areaDetail.allEvents': 'All Events',
        'areaDetail.temperature': 'Temperature',
        'areaDetail.heating': 'Heating',
        'areaDetail.schedule': 'Schedule',
        'areaDetail.smartBoost': 'Smart Boost',
        'areaDetail.sensors': 'Sensors',
        'areaDetail.mode': 'Mode',
        'settingsCards.noLogsYet': 'No logs yet',
      }
      return translations[key] || key
    },
  }),
}))

describe('AreaLogsTab', () => {
  const mockLogs: AreaLogEntry[] = [
    {
      timestamp: '2024-01-15T10:30:00Z',
      type: 'temperature',
      message: 'Temperature set to 21°C',
      details: { old_temp: 20, new_temp: 21 },
    },
    {
      timestamp: '2024-01-15T10:25:00Z',
      type: 'heating',
      message: 'Heating turned on',
      details: {},
    },
    {
      timestamp: '2024-01-15T10:20:00Z',
      type: 'schedule',
      message: 'Schedule activated: Morning',
      details: { schedule_id: 'morning' },
    },
  ]

  const mockOnFilterChange = vi.fn()
  const mockOnRefresh = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders without crashing', () => {
    render(
      <AreaLogsTab
        logs={mockLogs}
        logsLoading={false}
        logFilter="all"
        onFilterChange={mockOnFilterChange}
        onRefresh={mockOnRefresh}
      />,
    )
    expect(screen.getByText('Heating Strategy Logs')).toBeInTheDocument()
  })

  it('renders title and description', () => {
    render(
      <AreaLogsTab
        logs={[]}
        logsLoading={false}
        logFilter="all"
        onFilterChange={mockOnFilterChange}
        onRefresh={mockOnRefresh}
      />,
    )
    expect(screen.getByText('Heating Strategy Logs')).toBeInTheDocument()
    expect(screen.getByText('View heating strategy logs')).toBeInTheDocument()
  })

  it('shows refresh button', () => {
    render(
      <AreaLogsTab
        logs={[]}
        logsLoading={false}
        logFilter="all"
        onFilterChange={mockOnFilterChange}
        onRefresh={mockOnRefresh}
      />,
    )
    const refreshButton = screen.getByRole('button', { name: 'Refresh' })
    expect(refreshButton).toBeInTheDocument()
  })

  it('calls onRefresh when refresh button is clicked', () => {
    render(
      <AreaLogsTab
        logs={[]}
        logsLoading={false}
        logFilter="all"
        onFilterChange={mockOnFilterChange}
        onRefresh={mockOnRefresh}
      />,
    )
    const refreshButton = screen.getByRole('button', { name: 'Refresh' })
    fireEvent.click(refreshButton)
    expect(mockOnRefresh).toHaveBeenCalledTimes(1)
  })

  it('disables refresh button when loading', () => {
    render(
      <AreaLogsTab
        logs={[]}
        logsLoading={true}
        logFilter="all"
        onFilterChange={mockOnFilterChange}
        onRefresh={mockOnRefresh}
      />,
    )
    const refreshButton = screen.getByRole('button', { name: 'Loading...' })
    expect(refreshButton).toBeDisabled()
  })

  it('shows loading indicator when logsLoading is true', () => {
    render(
      <AreaLogsTab
        logs={[]}
        logsLoading={true}
        logFilter="all"
        onFilterChange={mockOnFilterChange}
        onRefresh={mockOnRefresh}
      />,
    )
    expect(screen.getByRole('progressbar')).toBeInTheDocument()
  })

  it('shows empty message when no logs', () => {
    render(
      <AreaLogsTab
        logs={[]}
        logsLoading={false}
        logFilter="all"
        onFilterChange={mockOnFilterChange}
        onRefresh={mockOnRefresh}
      />,
    )
    expect(screen.getByTestId('area-logs-empty')).toBeInTheDocument()
    expect(screen.getByText('No logs yet')).toBeInTheDocument()
  })

  it('renders filter chips', () => {
    render(
      <AreaLogsTab
        logs={[]}
        logsLoading={false}
        logFilter="all"
        onFilterChange={mockOnFilterChange}
        onRefresh={mockOnRefresh}
      />,
    )
    expect(screen.getByText('All Events')).toBeInTheDocument()
    expect(screen.getByText('Temperature')).toBeInTheDocument()
    expect(screen.getByText('Heating')).toBeInTheDocument()
    expect(screen.getByText('Schedule')).toBeInTheDocument()
    expect(screen.getByText('Smart Boost')).toBeInTheDocument()
    expect(screen.getByText('Sensors')).toBeInTheDocument()
    expect(screen.getByText('Mode')).toBeInTheDocument()
  })

  it('calls onFilterChange when filter chip is clicked', () => {
    render(
      <AreaLogsTab
        logs={[]}
        logsLoading={false}
        logFilter="all"
        onFilterChange={mockOnFilterChange}
        onRefresh={mockOnRefresh}
      />,
    )
    const temperatureChip = screen.getByText('Temperature')
    fireEvent.click(temperatureChip)
    expect(mockOnFilterChange).toHaveBeenCalledWith('temperature')
  })

  it('displays log entries', () => {
    render(
      <AreaLogsTab
        logs={mockLogs}
        logsLoading={false}
        logFilter="all"
        onFilterChange={mockOnFilterChange}
        onRefresh={mockOnRefresh}
      />,
    )
    expect(screen.getByText('Temperature set to 21°C')).toBeInTheDocument()
    expect(screen.getByText('Heating turned on')).toBeInTheDocument()
    expect(screen.getByText('Schedule activated: Morning')).toBeInTheDocument()
  })

  it('displays log type chips for each entry', () => {
    render(
      <AreaLogsTab
        logs={mockLogs}
        logsLoading={false}
        logFilter="all"
        onFilterChange={mockOnFilterChange}
        onRefresh={mockOnRefresh}
      />,
    )
    // Check that type chips are rendered (there are multiple "temperature", "heating", "schedule" text elements)
    const typeChips = screen.getAllByText(/temperature|heating|schedule/i)
    expect(typeChips.length).toBeGreaterThan(0)
  })

  it('displays log details when available', () => {
    render(
      <AreaLogsTab
        logs={mockLogs}
        logsLoading={false}
        logFilter="all"
        onFilterChange={mockOnFilterChange}
        onRefresh={mockOnRefresh}
      />,
    )
    // The details are rendered as JSON strings
    expect(screen.getByText(/"old_temp":/)).toBeInTheDocument()
    expect(screen.getByText(/"new_temp":/)).toBeInTheDocument()
  })

  it('does not display details for empty details object', () => {
    const logsWithEmptyDetails: AreaLogEntry[] = [
      {
        timestamp: '2024-01-15T10:25:00Z',
        type: 'heating',
        message: 'Heating turned on',
        details: {},
      },
    ]
    render(
      <AreaLogsTab
        logs={logsWithEmptyDetails}
        logsLoading={false}
        logFilter="all"
        onFilterChange={mockOnFilterChange}
        onRefresh={mockOnRefresh}
      />,
    )
    expect(screen.getByText('Heating turned on')).toBeInTheDocument()
    // Should not render the details section when details is empty
    const preElements = screen.queryAllByRole('generic')
    const hasDetailsBox = preElements.some(el => el.tagName === 'PRE')
    expect(hasDetailsBox).toBe(false)
  })

  it('renders dividers between log entries', () => {
    const { container } = render(
      <AreaLogsTab
        logs={mockLogs}
        logsLoading={false}
        logFilter="all"
        onFilterChange={mockOnFilterChange}
        onRefresh={mockOnRefresh}
      />,
    )
    const dividers = container.querySelectorAll('hr')
    // Should have dividers between entries (n-1 dividers for n entries)
    expect(dividers.length).toBe(mockLogs.length - 1)
  })

  it('formats timestamps correctly', () => {
    render(
      <AreaLogsTab
        logs={mockLogs}
        logsLoading={false}
        logFilter="all"
        onFilterChange={mockOnFilterChange}
        onRefresh={mockOnRefresh}
      />,
    )
    // Check that timestamps are rendered (they will be in nl-NL format)
    const timestamps = screen.getAllByText(/\d{1,2}:\d{2}:\d{2}/)
    expect(timestamps.length).toBeGreaterThan(0)
  })
})
