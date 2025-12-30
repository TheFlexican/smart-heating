import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import PreviewDialog from './ImportExportPreviewDialog'
import { vi } from 'vitest'

describe('PreviewDialog', () => {
  test('shows valid preview details and enables confirm', async () => {
    const onCancel = vi.fn()
    const onConfirm = vi.fn()
    const preview = {
      valid: true,
      version: '1.0.0',
      export_date: new Date().toISOString(),
      areas_to_create: 1,
      areas_to_update: 2,
      global_settings_included: true,
      vacation_mode_included: false,
    }

    render(
      <PreviewDialog
        open={true}
        preview={preview as any}
        onCancel={onCancel}
        onConfirm={onConfirm}
        loading={false}
        t={(k: string) => k}
      />,
    )

    expect(screen.getByText('importExport.previewTitle')).toBeInTheDocument()
    expect(screen.getByText('importExport.version')).toBeInTheDocument()
    expect(screen.getByText('importExport.exportDate')).toBeInTheDocument()
    expect(screen.getByText('importExport.areasToCreate')).toBeInTheDocument()
    expect(screen.getByText('importExport.areasToUpdate')).toBeInTheDocument()

    const confirm = screen.getByRole('button', { name: 'importExport.confirmImport' })
    await userEvent.click(confirm)
    expect(onConfirm).toHaveBeenCalled()
  })

  test('shows error when preview invalid and disables confirm', () => {
    const onCancel = vi.fn()
    const onConfirm = vi.fn()

    render(
      <PreviewDialog
        open={true}
        preview={{ valid: false, error: 'bad' }}
        onCancel={onCancel}
        onConfirm={onConfirm}
        loading={false}
        t={(k: string) => k}
      />,
    )

    expect(screen.getByText('bad')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'importExport.confirmImport' })).toBeDisabled()
  })
})
