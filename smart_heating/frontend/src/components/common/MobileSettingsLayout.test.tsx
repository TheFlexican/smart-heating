import React from 'react'
import { render, screen } from '@testing-library/react'
import { vi, describe, it, expect } from 'vitest'
import MobileSettingsLayout, { settingsItems } from './MobileSettingsLayout'

vi.mock('react-router-dom', () => ({ useNavigate: () => vi.fn() }))
vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string) => k }) }))

describe('MobileSettingsLayout', () => {
  it('renders list of settings items', () => {
    render(<MobileSettingsLayout />)

    // check a couple of known items by testId
    expect(screen.getByTestId(settingsItems[0].testId)).toBeInTheDocument()
    expect(screen.getByTestId(settingsItems[2].testId)).toBeInTheDocument()
  })
})
