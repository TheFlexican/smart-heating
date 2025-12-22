import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, it, expect } from 'vitest'
import { UserManagement } from './UserManagement'

vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string) => k }) }))
vi.mock('react-router-dom', () => ({ useNavigate: () => vi.fn() }))
vi.mock('../../api/users', () => ({
  getUsers: vi.fn().mockResolvedValue({ users: {} }),
  updateUserSettings: vi.fn(),
}))
vi.mock('../../api/config', () => ({ getPersonEntities: vi.fn().mockResolvedValue([]) }))

describe('UserManagement', () => {
  it('renders header buttons and opens dialogs', async () => {
    render(<UserManagement embedded={false} />)

    // header add/settings buttons should be present
    const addBtn = await screen.findByTestId('user-add-button')
    const settingsBtn = await screen.findByTestId('user-settings-button')

    expect(addBtn).toBeInTheDocument()
    expect(settingsBtn).toBeInTheDocument()

    const user = userEvent.setup()
    await user.click(addBtn)

    // after clicking add, the create dialog should appear with save/cancel
    expect(await screen.findByTestId('user-save')).toBeInTheDocument()
    expect(await screen.findByTestId('user-cancel')).toBeInTheDocument()

    // open settings
    await user.click(settingsBtn)
    expect(await screen.findByTestId('user-settings-strategy-select')).toBeInTheDocument()
  })
})
