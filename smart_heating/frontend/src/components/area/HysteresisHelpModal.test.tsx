import React from 'react'
import { render, screen } from '@testing-library/react'
import { vi, describe, it, expect } from 'vitest'
import HysteresisHelpModal from './HysteresisHelpModal'

vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string) => k }) }))

describe('HysteresisHelpModal', () => {
  it('renders content and close button', () => {
    const onClose = vi.fn()
    render(<HysteresisHelpModal open={true} onClose={onClose} />)

    expect(screen.getByText('hysteresisHelp.title')).toBeInTheDocument()
    expect(screen.getByTestId('hysteresis-help-close')).toBeInTheDocument()
  })
})
