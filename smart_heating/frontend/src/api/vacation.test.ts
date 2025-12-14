import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import * as v from './vacation'

vi.mock('axios')
const mockedAxios = axios as unknown as jest.Mocked<typeof axios>

describe('API - Vacation', () => {
  beforeEach(() => vi.clearAllMocks())

  it('get/enable/disable vacation mode', async () => {
    mockedAxios.get = vi.fn().mockResolvedValue({ data: { enabled: false } }) as any
    const vm = await v.getVacationMode()
    expect(vm.enabled).toBe(false)

    mockedAxios.post = vi.fn().mockResolvedValue({ data: { enabled: true } }) as any
    const enabled = await v.enableVacationMode({ start_date: '2022-01-01', end_date: '2022-01-10' })
    expect(enabled.enabled).toBe(true)

    mockedAxios.delete = vi.fn().mockResolvedValue({ data: { enabled: false } }) as any
    const disabled = await v.disableVacationMode()
    expect(disabled.enabled).toBe(false)
  })
})
