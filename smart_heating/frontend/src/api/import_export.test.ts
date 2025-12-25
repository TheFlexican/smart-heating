import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import * as imp from './import_export'

vi.mock('axios')
const mockedAxios = axios as unknown as jest.Mocked<typeof axios>

describe('API - Import/Export', () => {
  beforeEach(() => vi.clearAllMocks())

  it('export/import/validate and backups endpoints', async () => {
    const blob = new Blob(['ok'])
    mockedAxios.get = vi.fn().mockResolvedValue({ data: blob }) as any
    const exported = await imp.exportConfig()
    expect(exported).toBeTruthy()

    mockedAxios.post = vi.fn().mockResolvedValue({ data: { success: true } }) as any
    await imp.importConfig({})
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/smart_heating/import', {})
    await imp.validateConfig({})
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/smart_heating/validate', {})

    mockedAxios.get = vi.fn().mockResolvedValue({ data: { backups: [] } }) as any
    await imp.listBackups()
    expect(mockedAxios.get).toHaveBeenCalledWith('/api/smart_heating/backups')

    mockedAxios.post = vi.fn().mockResolvedValue({ data: { success: true } }) as any
    await imp.restoreBackup('file.json')
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/smart_heating/backups/file.json/restore')
  })
})
