import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import BoostControls from './BoostControls'
import { vi, describe, it, expect } from 'vitest'

vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string) => k }) }))
vi.mock('../../api/areas', () => ({ setBoostMode: vi.fn(), cancelBoost: vi.fn() }))
import * as areasApi from '../../api/areas'

describe('BoostControls', () => {
  it('shows disabled notice for airco areas', () => {
    const area = { id: 'a1', heating_type: 'airco' }
    const loadData = vi.fn()
    render(<BoostControls area={area as any} loadData={loadData} />)

    expect(screen.getByTestId('boost-mode-disabled-airco')).toBeInTheDocument()
  })

  it('activates boost and calls API and loadData', async () => {
    const area = { id: 'a1', heating_type: 'radiator' }
    const loadData = vi.fn().mockResolvedValue(undefined)
    render(<BoostControls area={area as any} loadData={loadData} />)

    const tempInput = screen.getByTestId('boost-temperature-input') as HTMLInputElement
    const durInput = screen.getByTestId('boost-duration-input') as HTMLInputElement
    const activate = screen.getByTestId('activate-boost-button')

    const tempNative = tempInput.querySelector('input') as HTMLInputElement
    const durNative = durInput.querySelector('input') as HTMLInputElement
    if (tempNative) fireEvent.change(tempNative, { target: { value: '24' } })
    if (durNative) fireEvent.change(durNative, { target: { value: '30' } })

    await userEvent.click(activate)

    expect(areasApi.setBoostMode).toHaveBeenCalledWith(area.id, 30, 24)
    expect(loadData).toHaveBeenCalled()
  })

  it('cancels active boost and calls API', async () => {
    const area = { id: 'a1', boost_mode_active: true, boost_temp: 25, boost_duration: 15 }
    const loadData = vi.fn().mockResolvedValue(undefined)
    render(<BoostControls area={area as any} loadData={loadData} />)

    const cancelBtn = screen.getByTestId('cancel-boost-button')
    await userEvent.click(cancelBtn)

    expect(areasApi.cancelBoost).toHaveBeenCalledWith(area.id)
    expect(loadData).toHaveBeenCalled()
  })
})
