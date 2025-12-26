import { render, screen } from '@testing-library/react'
import { vi } from 'vitest'
import { AreaScheduleTab } from './AreaScheduleTab'
import { Zone } from '../../types'

// Mock ScheduleEditor component
vi.mock('../ScheduleEditor', () => ({
  default: ({ area, onUpdate }: { area: Zone; onUpdate: () => void }) => (
    <div data-testid="schedule-editor">
      <div data-testid="schedule-editor-area-id">{area.id}</div>
      <button data-testid="schedule-editor-update" onClick={onUpdate}>
        Update
      </button>
    </div>
  ),
}))

describe('AreaScheduleTab', () => {
  const mockArea: Zone = {
    id: 'living_room',
    name: 'Living Room',
    state: 'heating',
    enabled: true,
    target_temperature: 21.0,
    current_temperature: 20.5,
    preset_mode: 'none',
    devices: [],
    schedules: [
      {
        id: 'schedule1',
        temperature: 20.0,
        time: '08:00',
        days: ['Monday', 'Tuesday'],
      },
    ],
  } as Zone

  const mockOnUpdate = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders without crashing', () => {
    render(<AreaScheduleTab area={mockArea} onUpdate={mockOnUpdate} />)
    expect(screen.getByTestId('schedule-editor')).toBeInTheDocument()
  })

  it('passes area prop to ScheduleEditor', () => {
    render(<AreaScheduleTab area={mockArea} onUpdate={mockOnUpdate} />)
    expect(screen.getByTestId('schedule-editor-area-id')).toHaveTextContent('living_room')
  })

  it('passes onUpdate callback to ScheduleEditor', () => {
    render(<AreaScheduleTab area={mockArea} onUpdate={mockOnUpdate} />)
    const updateButton = screen.getByTestId('schedule-editor-update')
    updateButton.click()
    expect(mockOnUpdate).toHaveBeenCalledTimes(1)
  })

  it('applies correct styling to container Box', () => {
    const { container } = render(<AreaScheduleTab area={mockArea} onUpdate={mockOnUpdate} />)
    const box = container.firstChild as HTMLElement
    expect(box).toHaveStyle({ maxWidth: '1200px' })
  })
})
