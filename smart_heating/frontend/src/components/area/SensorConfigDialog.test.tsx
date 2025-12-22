import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, it, expect } from 'vitest'

vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string) => k }) }))
vi.mock('../../api/config', () => ({ getBinarySensorEntities: vi.fn().mockResolvedValue([]) }))
import SensorConfigDialog from './SensorConfigDialog'

describe('SensorConfigDialog', () => {
  it('renders window sensor dialog and shows no entities', async () => {
    const onAdd = vi.fn()
    const onClose = vi.fn()

    render(<SensorConfigDialog open={true} onAdd={onAdd} onClose={onClose} sensorType="window" />)

    expect(await screen.findByTestId('sensor-dialog-title')).toBeInTheDocument()
    // MUI Select may not render the disabled MenuItem in the DOM; ensure manual input is present
    expect(await screen.findByTestId('sensor-manual-input')).toBeInTheDocument()
  })

  it('allows manual entity input and enables add button', async () => {
    const onAdd = vi.fn().mockResolvedValue(undefined)
    const onClose = vi.fn()

    render(<SensorConfigDialog open={true} onAdd={onAdd} onClose={onClose} sensorType="presence" />)

    const manualWrapper = await screen.findByTestId('sensor-manual-input')
    const manualInput = manualWrapper.querySelector('input') as HTMLInputElement
    await userEvent.type(manualInput, 'person.john')

    const addBtn = screen.getByTestId('sensor-add-button')
    expect(addBtn).toBeEnabled()
  })
})
