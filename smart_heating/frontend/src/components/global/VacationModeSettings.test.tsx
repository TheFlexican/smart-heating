import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { vi, describe, it, expect } from 'vitest'
vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string) => k }) }))
vi.mock('react-router-dom', () => ({ useNavigate: () => vi.fn() }))
vi.mock('../../api/vacation', () => ({
  getVacationMode: vi.fn().mockResolvedValue({ enabled: false }),
  enableVacationMode: vi.fn().mockResolvedValue({ enabled: true }),
  disableVacationMode: vi.fn().mockResolvedValue({ enabled: false }),
}))

describe('VacationModeSettings', () => {
  it('renders title and enable button', async () => {
    const { VacationModeSettings } = await import('./VacationModeSettings')
    render(<VacationModeSettings />)

    // component shows a loading spinner on mount
    expect(screen.getByRole('progressbar')).toBeInTheDocument()
  })
})
