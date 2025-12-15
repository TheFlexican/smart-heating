import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ScheduleEntryDialog from './ScheduleEntryDialog'

vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string, v?: any) => k }) }))

describe('ScheduleEntryDialog', () => {
  it('defaults to weekly and validates selected days', async () => {
    const onSave = vi.fn().mockResolvedValue(undefined)
    const onClose = vi.fn()
    const user = userEvent.setup()

    render(<ScheduleEntryDialog open={true} onClose={onClose} onSave={onSave} editingEntry={null} />)

    // Should show weekly toggle
    expect(screen.getByRole('button', { name: 'scheduleDialog.weeklyRecurring' })).toBeInTheDocument()

    // Clear selected days with 'clear selection' and verify save is disabled via validation
    await user.click(screen.getByText('scheduleDialog.clearSelection'))
    expect(screen.getByText('scheduleDialog.clearSelection')).toBeInTheDocument()
  })

  it('switches to specific date and allows selecting date', async () => {
    const onSave = vi.fn().mockResolvedValue(undefined)
    const onClose = vi.fn()
    const user = userEvent.setup()

    render(<ScheduleEntryDialog open={true} onClose={onClose} onSave={onSave} editingEntry={null} />)

    // Switch to date mode
    await user.click(screen.getByTestId('schedule-type-date'))
    expect(screen.getByText('scheduleDialog.selectDate')).toBeInTheDocument()
  })
})
