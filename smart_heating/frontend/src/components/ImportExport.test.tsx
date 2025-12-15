/// <reference types="vitest" />
import React from 'react'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import ImportExport from './ImportExport'
import { vi } from 'vitest'

// Mock translation
vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string) => k }) }))

// Mock react-router navigate
vi.mock('react-router-dom', () => ({ useNavigate: () => vi.fn() }))

describe('ImportExport', () => {
  it('renders export button and triggers fetch on click', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: { get: () => 'filename="test.json"' },
      blob: () => Promise.resolve(new Blob(['{}'], { type: 'application/json' }))
    })
    // @ts-ignore
    globalThis.fetch = mockFetch

    render(<ImportExport />)

    const btn = screen.getByTestId('import-export-button')
    expect(btn).toBeInTheDocument()

    fireEvent.click(btn)

    await waitFor(() => expect(mockFetch).toHaveBeenCalled())
  })
})
