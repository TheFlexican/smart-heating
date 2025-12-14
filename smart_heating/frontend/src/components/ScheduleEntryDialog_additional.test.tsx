import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, it, expect } from 'vitest'
import ScheduleEntryDialog from './ScheduleEntryDialog'

vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string) => k }) }))

describe('ScheduleEntryDialog additional behaviors', () => {
  it('validations for weekly days and allDays quick select', async () => {
    const onSave = vi.fn().mockResolvedValue(undefined)
    const onClose = vi.fn()
    const user = userEvent.setup()

    render(<ScheduleEntryDialog open={true} onClose={onClose} onSave={onSave} editingEntry={null} />)

    // Initially Save should be enabled (Monday selected)
    const saveBtn = screen.getByRole('button', { name: 'common.save' })
    expect(saveBtn).toBeEnabled()

    // Clear all selection
    await user.click(screen.getByRole('button', { name: 'scheduleDialog.clearSelection' }))
    expect(saveBtn).toBeDisabled()

    // Select all days and verify chips are present
    await user.click(screen.getByRole('button', { name: 'scheduleDialog.allDays' }))
    expect(saveBtn).toBeEnabled()
    // expected to have a chip for Monday
    expect(screen.getByText('Monday')).toBeInTheDocument()
  })

  it('date schedule includes date in save entry', async () => {
    const onSave = vi.fn().mockResolvedValue(undefined)
    const onClose = vi.fn()
    const user = userEvent.setup()
    render(<ScheduleEntryDialog open={true} onClose={onClose} onSave={onSave} editingEntry={null} />)

    await user.click(screen.getByRole('button', { name: 'scheduleDialog.specificDate' }))
    // clicking Save should include a date
    await user.click(screen.getByRole('button', { name: 'common.save' }))
    expect(onSave).toHaveBeenCalled()
    const entry = onSave.mock.calls[0][0]
    expect(entry.date).toBeDefined()
  })

  it('prefilled editingEntry with preset_mode writes preset in entry', async () => {
    const onSave = vi.fn().mockResolvedValue(undefined)
    const onClose = vi.fn()
    const editingEntry = { id: 'e1', start_time: '06:00', end_time: '07:00', days: ['Monday'], preset_mode: 'eco' }
    render(<ScheduleEntryDialog open={true} onClose={onClose} onSave={onSave} editingEntry={editingEntry as any} />)
    await userEvent.click(screen.getByRole('button', { name: 'common.save' }))
    expect(onSave).toHaveBeenCalled()
    const entry = onSave.mock.calls[0][0]
    expect(entry.preset_mode).toBe('eco')
  })
})
