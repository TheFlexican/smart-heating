import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ExportButton from './ExportButton'

describe('ExportButton', () => {
  test('renders and calls onExport when clicked', async () => {
    const mockFactory = (globalThis as any).vi?.fn ?? (globalThis as any).jest?.fn
    const onExport = mockFactory()
    render(<ExportButton loading={false} onExport={onExport} t={(k: string) => k} />)

    const btn = screen.getByTestId('import-export-button')
    await userEvent.click(btn)
    expect(onExport).toHaveBeenCalled()
  })

  test('is disabled when loading', () => {
    const mockFactory = (globalThis as any).vi?.fn ?? (globalThis as any).jest?.fn
    const onExport = mockFactory()
    render(<ExportButton loading={true} onExport={onExport} t={(k: string) => k} />)

    expect(screen.getByTestId('import-export-button')).toBeDisabled()
  })
})
