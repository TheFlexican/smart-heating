import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, it, expect } from 'vitest'
import AutoPresetControls from './AutoPresetControls'

vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string) => k }) }))

describe('AutoPresetControls', () => {
  it('shows disabled warning when auto_preset_enabled is false', () => {
    const area = { id: 'a1', auto_preset_enabled: false }
    render(<AutoPresetControls area={area as any} loadData={vi.fn()} />)

    expect(screen.getByText('settingsCards.autoPresetDisabled')).toBeInTheDocument()
  })

  it('calls fetch and loadData when preset changed', async () => {
    const area = { id: 'a1', auto_preset_enabled: true, auto_preset_home: 'home' }
    const loadData = vi.fn().mockResolvedValue(undefined)
    const fetchMock = vi.fn().mockResolvedValue({ ok: true })
    vi.stubGlobal('fetch', fetchMock)

    render(<AutoPresetControls area={area as any} loadData={loadData} />)

    // find the select element and change its native input value
    const select = screen.getByText('settingsCards.presetHome')
    const combobox = select.closest('[role="combobox"]')
    if (combobox) {
      await userEvent.click(combobox)
      // choose comfort option
      const option = await screen.findByText('settingsCards.presetComfort')
      await userEvent.click(option)

      expect(fetchMock).toHaveBeenCalled()
      expect(loadData).toHaveBeenCalled()
    }
  })
})
