import React from 'react'
import { render, screen } from '@testing-library/react'
import ImportExportNotifications from './ImportExportNotifications'

describe('ImportExportNotifications', () => {
  test('shows error alert when error provided', () => {
    const mockFactory = (globalThis as any).vi?.fn ?? (globalThis as any).jest?.fn
    const setError = mockFactory()
    render(
      <ImportExportNotifications
        error="bad"
        success={null}
        setError={setError}
        setSuccess={() => {}}
      />,
    )

    expect(screen.getByText('bad')).toBeInTheDocument()
  })

  test('shows success alert and renders message lines', () => {
    const mockFactory = (globalThis as any).vi?.fn ?? (globalThis as any).jest?.fn
    const setSuccess = mockFactory()
    const msg = 'ok\nline2'
    render(
      <ImportExportNotifications
        error={null}
        success={msg}
        setError={() => {}}
        setSuccess={setSuccess}
      />,
    )

    expect(screen.getByText('ok')).toBeInTheDocument()
    expect(screen.getByText('line2')).toBeInTheDocument()
  })
})
