import { describe, it, expect, vi, beforeEach } from 'vitest'
import { apiClient } from './client'
import * as v from './vacation'

vi.mock('./client')
const mockedClient = vi.mocked(apiClient)

describe('API - Vacation', () => {
  beforeEach(() => vi.clearAllMocks())

  it('get/enable/disable vacation mode', async () => {
    mockedClient.get.mockResolvedValue({ data: { enabled: false } } as any)
    const vm = await v.getVacationMode()
    expect(vm.enabled).toBe(false)

    mockedClient.post.mockResolvedValue({ data: { enabled: true } } as any)
    const enabled = await v.enableVacationMode({ start_date: '2022-01-01', end_date: '2022-01-10' })
    expect(enabled.enabled).toBe(true)

    mockedClient.delete.mockResolvedValue({ data: { enabled: false } } as any)
    const disabled = await v.disableVacationMode()
    expect(disabled.enabled).toBe(false)
  })
})
