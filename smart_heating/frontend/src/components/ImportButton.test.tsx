import React from 'react'
import { render, screen } from '@testing-library/react'
import ImportButton from './ImportButton'

describe('ImportButton', () => {
  test('renders and exposes file input', async () => {
    const mockFactory = (globalThis as any).vi?.fn ?? (globalThis as any).jest?.fn
    const onFileSelect = mockFactory()
    render(<ImportButton loading={false} onFileSelect={onFileSelect} t={(k: string) => k} />)

    const btn = screen.getByTestId('import-file-button')
    expect(btn).toBeInTheDocument()

    const input = btn.querySelector('input[type=file]')
    expect(input).toBeInTheDocument()
  })

  test('is disabled when loading', () => {
    render(<ImportButton loading={true} onFileSelect={() => {}} t={(k: string) => k} />)
    expect(screen.getByTestId('import-file-button')).toHaveAttribute('aria-disabled', 'true')
  })
})
