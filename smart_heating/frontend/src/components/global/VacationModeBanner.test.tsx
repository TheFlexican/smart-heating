import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, it, expect } from 'vitest'
import { VacationModeBanner } from './VacationModeBanner'

vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string) => k }) }))
vi.mock('../../api/vacation', () => ({
  getVacationMode: vi.fn(),
  disableVacationMode: vi.fn(),
}))
import * as api from '../../api/vacation'

describe('VacationModeBanner', () => {
  it('renders when vacation mode enabled and calls disable', async () => {
    vi.spyOn(api, 'getVacationMode').mockResolvedValue({ enabled: true, preset_mode: 'away' })
    const disableSpy = vi.spyOn(api, 'disableVacationMode').mockResolvedValue({ enabled: false })

    render(<VacationModeBanner />)

    expect(await screen.findByText('vacation.active')).toBeInTheDocument()

    const btn = await screen.findByTestId('vacation-disable-button')
    await userEvent.click(btn)

    expect(disableSpy).toHaveBeenCalled()
  })
})
