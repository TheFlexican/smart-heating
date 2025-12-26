import { render, screen } from '@testing-library/react'
import { vi } from 'vitest'
import { AreaHistoryTab } from './AreaHistoryTab'

// Mock HistoryChart component
vi.mock('../HistoryChart', () => ({
  default: ({ areaId }: { areaId: string }) => (
    <div data-testid="history-chart">
      <div data-testid="history-chart-area-id">{areaId}</div>
    </div>
  ),
}))

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        'areaDetail.temperatureHistory': 'Temperature History',
        'areaDetail.historyDescription': 'View historical temperature data',
      }
      return translations[key] || key
    },
  }),
}))

describe('AreaHistoryTab', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders without crashing', () => {
    render(<AreaHistoryTab areaId="living_room" />)
    expect(screen.getByTestId('history-chart')).toBeInTheDocument()
  })

  it('passes areaId prop to HistoryChart', () => {
    render(<AreaHistoryTab areaId="living_room" />)
    expect(screen.getByTestId('history-chart-area-id')).toHaveTextContent('living_room')
  })

  it('renders title and description', () => {
    render(<AreaHistoryTab areaId="living_room" />)
    expect(screen.getByText('Temperature History')).toBeInTheDocument()
    expect(screen.getByText('View historical temperature data')).toBeInTheDocument()
  })

  it('renders HistoryIcon', () => {
    const { container } = render(<AreaHistoryTab areaId="living_room" />)
    const icon = container.querySelector('[data-testid="HistoryIcon"]')
    expect(icon).toBeInTheDocument()
  })

  it('conditionally renders HistoryChart only when areaId is provided', () => {
    const { rerender } = render(<AreaHistoryTab areaId="living_room" />)
    expect(screen.getByTestId('history-chart')).toBeInTheDocument()

    // Test with empty areaId
    rerender(<AreaHistoryTab areaId="" />)
    expect(screen.queryByTestId('history-chart')).not.toBeInTheDocument()
  })
})
