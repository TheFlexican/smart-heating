/// <reference types="vitest" />
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import ScheduleEditor from './ScheduleEditor'

vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string) => k }) }))

// Mock nested ScheduleEntryDialog to avoid MUI DatePicker complexity
vi.mock('./ScheduleEntryDialog', () => ({
  __esModule: true,
  default: ({ open, onClose, onSave, editingEntry }: any) => (
    open ? (
      <div>
        <button onClick={() => onSave({ id: 'from-test', start_time: '06:00', end_time: '07:00', days: ['Monday'], temperature: 20 })}>Save</button>
        <button onClick={onClose}>Close</button>
      </div>
    ) : null
  )
}))

vi.mock('../api/areas', () => ({
  addScheduleToZone: vi.fn().mockResolvedValue({}),
  removeScheduleFromZone: vi.fn().mockResolvedValue(undefined),
  updateScheduleInZone: vi.fn().mockResolvedValue(undefined),
}))

describe('ScheduleEditor', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows empty schedule message when no schedules', () => {
    const area = { id: 'a1', name: 'Test Area', schedules: [] }
    render(<ScheduleEditor area={area as any} onUpdate={() => {}} />)

    expect(screen.getByText('areaDetail.noSchedulesConfigured')).toBeInTheDocument()
  })

  it('renders weekly and date schedules and can delete', async () => {
    const daySchedule = { id: 's1', day: 'Monday', start_time: '06:00', end_time: '07:00', temperature: 20 }
    const weeklySchedule = { id: 's2', days: ['Monday', 'Tuesday'], start_time: '06:00', end_time: '07:00', temperature: 21 }
    const dateSchedule = { id: 's3', date: '2024-04-01', start_time: '08:00', end_time: '09:00', temperature: 19 }
    const area = { id: 'a1', name: 'Test Area', schedules: [daySchedule, weeklySchedule, dateSchedule] }
    const onUpdate = vi.fn()
    render(<ScheduleEditor area={area as any} onUpdate={onUpdate} />)

    expect(screen.getByText(/2024/)).toBeInTheDocument()

    const deleteIcons = Array.from(document.querySelectorAll('.MuiChip-deleteIcon, svg[data-testid="DeleteIcon"]'))
    expect(deleteIcons.length).toBeGreaterThanOrEqual(3)
    expect(deleteIcons.some((el: any) => el.closest('.MuiChip-root')?.textContent?.includes('08:00 - 09:00'))).toBeTruthy()
    expect(deleteIcons.some((el: any) => el.closest('.MuiChip-root')?.textContent?.includes('06:00 - 07:00'))).toBeTruthy()
  })

  it('opens dialog for adding schedules and calls onSave', async () => {
    const area = { id: 'a1', name: 'Test Area', schedules: [] }
    const onUpdate = vi.fn()
    const user = userEvent.setup()
    render(<ScheduleEditor area={area as any} onUpdate={onUpdate} />)

    await user.click(screen.getByRole('button', { name: 'areaDetail.addSchedule' }))
    const saveButton = screen.getByText('Save')
    await user.click(saveButton)
    const { addScheduleToZone } = await import('../api/areas')
    expect(addScheduleToZone).toHaveBeenCalled()
    expect(onUpdate).toHaveBeenCalled()
  })
})
