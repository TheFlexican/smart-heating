import { describe, it, expect, vi, beforeEach } from 'vitest'
import { apiClient } from './client'
import * as presets from './presets'

vi.mock('./client')
const mockedClient = vi.mocked(apiClient)

describe('API - Presets', () => {
  beforeEach(() => vi.clearAllMocks())

  it('get and set global presets', async () => {
    mockedClient.get.mockResolvedValue({ data: { presets: [] } } as any)
    const gp = await presets.getGlobalPresets()
    expect(gp.presets).toBeDefined()

    mockedClient.post.mockResolvedValue({ data: {} } as any)
    await presets.setGlobalPresets({ test: true })
    expect(mockedClient.post).toHaveBeenCalledWith('/global_presets', {
      test: true,
    })
  })
})
