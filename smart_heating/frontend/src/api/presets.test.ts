import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import * as presets from './presets'

vi.mock('axios')
const mockedAxios = axios as unknown as jest.Mocked<typeof axios>

describe('API - Presets', () => {
  beforeEach(() => vi.clearAllMocks())

  it('get and set global presets', async () => {
    mockedAxios.get = vi.fn().mockResolvedValue({ data: { presets: [] } }) as any
    const gp = await presets.getGlobalPresets()
    expect(gp.presets).toBeDefined()

    mockedAxios.post = vi.fn().mockResolvedValue({ data: {} }) as any
    await presets.setGlobalPresets({ test: true })
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/smart_heating/global_presets', { test: true })
  })
})
