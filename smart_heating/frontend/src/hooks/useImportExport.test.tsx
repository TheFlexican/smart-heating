import React from 'react'
import { render, screen, act, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
let useImportExport: any

function TestHarness() {
  const t = (k: string) => k
  const hook = useImportExport(t)

  return (
    <div>
      <button onClick={() => hook.handleExport()} data-testid="do-export">
        export
      </button>
      <input type="file" data-testid="file-input" onChange={hook.handleFileSelect} />
      <button onClick={() => hook.handleConfirmImport()} data-testid="confirm-import">
        confirm
      </button>
      <div data-testid="loading">{String(hook.loading)}</div>
      <div data-testid="error">{hook.error ?? ''}</div>
      <div data-testid="success">{hook.success ?? ''}</div>
      <div data-testid="preview">{hook.preview ? JSON.stringify(hook.preview) : ''}</div>
      <div data-testid="showPreview">{String(hook.showPreviewDialog)}</div>
    </div>
  )
}

describe('useImportExport', () => {
  beforeEach(async () => {
    const mockFactory = (globalThis as any).vi?.fn ?? (globalThis as any).jest?.fn
    const clearMocks = () => {
      if ((globalThis as any).vi) (globalThis as any).vi.clearAllMocks()
      else (globalThis as any).jest.clearAllMocks()
    }

    // dynamically mock the import_export API functions (ES modules are read-only)
    if ((globalThis as any).vi) {
      ;(globalThis as any).vi.mock('../api/import_export', () => ({
        importConfig: mockFactory().mockResolvedValue({ success: true }),
        validateConfig: mockFactory().mockResolvedValue({ valid: true, version: '1.0' }),
      }))
    } else {
      ;(globalThis as any).jest.mock('../api/import_export', () => ({
        importConfig: mockFactory().mockResolvedValue({ success: true }),
        validateConfig: mockFactory().mockResolvedValue({ valid: true, version: '1.0' }),
      }))
    }

    // ensure hook module is loaded after mocks
    const hookMod = await import('./useImportExport')
    useImportExport = hookMod.default

    clearMocks()
    ;(globalThis as any).location = { reload: mockFactory() }
  })

  test('handleExport success sets success message', async () => {
    const blob = new Blob(['{}'], { type: 'application/json' })
    const mockFactory = (globalThis as any).vi?.fn ?? (globalThis as any).jest?.fn
    globalThis.fetch = mockFactory().mockResolvedValue({
      ok: true,
      headers: { get: () => 'attachment; filename="test.json"' },
      blob: async () => blob,
    })
    globalThis.URL.createObjectURL = mockFactory().mockReturnValue('blob:123')
    globalThis.URL.revokeObjectURL = mockFactory()

    render(<TestHarness />)

    await act(async () => {
      userEvent.click(screen.getByTestId('do-export'))
    })

    // wait for async update
    await waitFor(() =>
      expect(screen.getByTestId('success').textContent).toContain('importExport.exportSuccess'),
    )
  })

  test('handleFileSelect reads file and shows preview', async () => {
    const file = new File([JSON.stringify({ foo: 'bar' })], 'test.json', {
      type: 'application/json',
    })
    ;(file as any).text = async () => JSON.stringify({ foo: 'bar' })
    const api = await import('../api/import_export')
    api.validateConfig.mockResolvedValue({ valid: true, version: '1.0' })

    render(<TestHarness />)

    // simulate input change event via userEvent
    const input = screen.getByTestId('file-input') as HTMLInputElement
    await act(async () => {
      await userEvent.upload(input, file)
    })

    await waitFor(() => expect(screen.getByTestId('showPreview').textContent).toBe('true'))
    expect(screen.getByTestId('preview').textContent).toContain('"version":"1.0"')
  })

  test('confirm import success shows formatted success and reloads', async () => {
    const file = new File([JSON.stringify({ foo: 'bar' })], 'test.json', {
      type: 'application/json',
    })
    ;(file as any).text = async () => JSON.stringify({ foo: 'bar' })
    const api = await import('../api/import_export')
    api.validateConfig.mockResolvedValue({ valid: true })
    api.importConfig.mockResolvedValue({
      success: true,
      changes: {
        areas_created: 1,
        areas_updated: 0,
        global_settings_updated: true,
        vacation_mode_updated: false,
      },
    })

    render(<TestHarness />)

    // select file
    const input = screen.getByTestId('file-input') as HTMLInputElement
    await act(async () => {
      await userEvent.upload(input, file)
    })

    // confirm
    await act(async () => {
      userEvent.click(screen.getByTestId('confirm-import'))
    })

    await waitFor(() =>
      expect(screen.getByTestId('success').textContent).toContain('importExport.importSuccess'),
    )

    // wait for reload to be triggered (reload happens ~2s after success)
    await waitFor(() => expect((globalThis as any).location.reload).toHaveBeenCalled(), {
      timeout: 3000,
    })
  })
})
