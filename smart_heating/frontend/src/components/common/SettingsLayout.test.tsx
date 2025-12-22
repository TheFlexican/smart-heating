import React from 'react'
import { render, screen } from '@testing-library/react'
import { vi, describe, it, expect } from 'vitest'
import SettingsLayout from './SettingsLayout'

vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string) => k }) }))
vi.mock('react-router-dom', () => ({
  useLocation: () => ({ pathname: '/settings' }),
  useNavigate: () => vi.fn(),
}))
vi.mock('@mui/material', async () => {
  const actual = await vi.importActual('@mui/material')
  return { ...actual, useMediaQuery: () => true }
})

describe('SettingsLayout', () => {
  it('renders MobileSettingsLayout on mobile /settings route', () => {
    render(<SettingsLayout themeMode="light" onThemeChange={() => {}} />)
    expect(screen.getByText('Settings')).toBeInTheDocument()
  })
})
