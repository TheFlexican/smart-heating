import { describe, it, expect, vi, beforeEach } from 'vitest'
import { apiClient } from './client'
import * as imp from './import_export'

vi.mock('./client')
const mockedClient = vi.mocked(apiClient)

describe('API - Import/Export', () => {
  beforeEach(() => vi.clearAllMocks())

  it('export/import/validate and backups endpoints', async () => {
    const blob = new Blob(['ok'])
    mockedClient.get.mockResolvedValue({ data: blob } as any)
    const exported = await imp.exportConfig()
    expect(exported).toBeTruthy()

    mockedClient.post.mockResolvedValue({ data: { success: true } } as any)
    await imp.importConfig({})
    expect(mockedClient.post).toHaveBeenCalledWith('/import', {})
    await imp.validateConfig({})
    expect(mockedClient.post).toHaveBeenCalledWith('/validate', {})

    mockedClient.get.mockResolvedValue({ data: { backups: [] } } as any)
    await imp.listBackups()
    expect(mockedClient.get).toHaveBeenCalledWith('/backups')

    mockedClient.post.mockResolvedValue({ data: { success: true } } as any)
    await imp.restoreBackup('file.json')
    expect(mockedClient.post).toHaveBeenCalledWith('/backups/file.json/restore')
  })
})
