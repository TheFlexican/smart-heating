import { describe, it, expect, vi, beforeEach } from 'vitest'
import { apiClient } from './client'
import { setAreaPid } from './areas'

vi.mock('./client')
const mockedClient = vi.mocked(apiClient)

describe('API - setAreaPid', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Basic Functionality', () => {
    it('calls POST endpoint with correct URL', async () => {
      mockedClient.post.mockResolvedValue({ data: {} } as any)

      await setAreaPid('living_room', true, true, ['schedule'])

      expect(mockedClient.post).toHaveBeenCalledWith('/areas/living_room/pid', expect.any(Object))
    })

    it('sends all three parameters in request body', async () => {
      mockedClient.post.mockResolvedValue({ data: {} } as any)

      await setAreaPid('bedroom', false, true, ['home', 'away'])

      expect(mockedClient.post).toHaveBeenCalledWith('/areas/bedroom/pid', {
        enabled: false,
        automatic_gains: true,
        active_modes: ['home', 'away'],
      })
    })

    it('uses snake_case for automatic_gains parameter', async () => {
      mockedClient.post.mockResolvedValue({ data: {} } as any)

      await setAreaPid('office', true, false, ['schedule'])

      const callArgs = mockedClient.post.mock.calls[0][1]
      expect(callArgs).toHaveProperty('automatic_gains', false)
      expect(callArgs).not.toHaveProperty('automaticGains')
    })

    it('uses snake_case for active_modes parameter', async () => {
      mockedClient.post.mockResolvedValue({ data: {} } as any)

      await setAreaPid('kitchen', true, true, ['comfort'])

      const callArgs = mockedClient.post.mock.calls[0][1]
      expect(callArgs).toHaveProperty('active_modes', ['comfort'])
      expect(callArgs).not.toHaveProperty('activeModes')
    })
  })

  describe('Parameter Variations', () => {
    it('handles PID enabled with automatic gains enabled', async () => {
      mockedClient.post.mockResolvedValue({ data: {} } as any)

      await setAreaPid('area1', true, true, ['schedule', 'home'])

      expect(mockedClient.post).toHaveBeenCalledWith('/areas/area1/pid', {
        enabled: true,
        automatic_gains: true,
        active_modes: ['schedule', 'home'],
      })
    })

    it('handles PID enabled with automatic gains disabled (manual)', async () => {
      mockedClient.post.mockResolvedValue({ data: {} } as any)

      await setAreaPid('area2', true, false, ['home', 'comfort'])

      expect(mockedClient.post).toHaveBeenCalledWith('/areas/area2/pid', {
        enabled: true,
        automatic_gains: false,
        active_modes: ['home', 'comfort'],
      })
    })

    it('handles PID disabled (other parameters still sent)', async () => {
      mockedClient.post.mockResolvedValue({ data: {} } as any)

      await setAreaPid('area3', false, true, ['schedule'])

      expect(mockedClient.post).toHaveBeenCalledWith('/areas/area3/pid', {
        enabled: false,
        automatic_gains: true,
        active_modes: ['schedule'],
      })
    })

    it('handles empty active modes array', async () => {
      mockedClient.post.mockResolvedValue({ data: {} } as any)

      await setAreaPid('area4', true, true, [])

      expect(mockedClient.post).toHaveBeenCalledWith('/areas/area4/pid', {
        enabled: true,
        automatic_gains: true,
        active_modes: [],
      })
    })

    it('handles single active mode', async () => {
      mockedClient.post.mockResolvedValue({ data: {} } as any)

      await setAreaPid('area5', true, false, ['boost'])

      expect(mockedClient.post).toHaveBeenCalledWith('/areas/area5/pid', {
        enabled: true,
        automatic_gains: false,
        active_modes: ['boost'],
      })
    })

    it('handles all available modes', async () => {
      mockedClient.post.mockResolvedValue({ data: {} } as any)

      const allModes = ['schedule', 'home', 'away', 'sleep', 'comfort', 'eco', 'boost']
      await setAreaPid('area6', true, true, allModes)

      expect(mockedClient.post).toHaveBeenCalledWith('/areas/area6/pid', {
        enabled: true,
        automatic_gains: true,
        active_modes: allModes,
      })
    })
  })

  describe('Area ID Handling', () => {
    it('handles area ID with underscores', async () => {
      mockedClient.post.mockResolvedValue({ data: {} } as any)

      await setAreaPid('living_room', true, true, ['home'])

      expect(mockedClient.post).toHaveBeenCalledWith('/areas/living_room/pid', expect.any(Object))
    })

    it('handles area ID with hyphens', async () => {
      mockedClient.post.mockResolvedValue({ data: {} } as any)

      await setAreaPid('guest-bedroom', true, true, ['away'])

      expect(mockedClient.post).toHaveBeenCalledWith('/areas/guest-bedroom/pid', expect.any(Object))
    })

    it('handles numeric area ID', async () => {
      mockedClient.post.mockResolvedValue({ data: {} } as any)

      await setAreaPid('12345', true, true, ['home'])

      expect(mockedClient.post).toHaveBeenCalledWith('/areas/12345/pid', expect.any(Object))
    })

    it('handles area ID with special characters', async () => {
      mockedClient.post.mockResolvedValue({ data: {} } as any)

      await setAreaPid('area.test_1', false, false, ['schedule'])

      expect(mockedClient.post).toHaveBeenCalledWith('/areas/area.test_1/pid', expect.any(Object))
    })
  })

  describe('Error Handling', () => {
    it('propagates API errors', async () => {
      const apiError = new Error('API Error')
      mockedClient.post.mockRejectedValue(apiError)

      await expect(setAreaPid('area1', true, true, ['schedule'])).rejects.toThrow('API Error')
    })

    it('propagates network errors', async () => {
      const networkError = new Error('Network Error')
      mockedClient.post.mockRejectedValue(networkError)

      await expect(setAreaPid('area2', false, false, ['home'])).rejects.toThrow('Network Error')
    })

    it('propagates 404 errors', async () => {
      const notFoundError = { response: { status: 404, data: { error: 'Area not found' } } }
      mockedClient.post.mockRejectedValue(notFoundError)

      await expect(setAreaPid('nonexistent', true, true, ['schedule'])).rejects.toEqual(
        notFoundError,
      )
    })

    it('propagates 500 server errors', async () => {
      const serverError = { response: { status: 500, data: { error: 'Internal server error' } } }
      mockedClient.post.mockRejectedValue(serverError)

      await expect(setAreaPid('area1', true, true, ['home'])).rejects.toEqual(serverError)
    })
  })

  describe('Return Value', () => {
    it('returns void (Promise<void>)', async () => {
      mockedClient.post.mockResolvedValue({ data: { success: true } } as any)

      const result = await setAreaPid('area1', true, true, ['schedule'])

      expect(result).toBeUndefined()
    })

    it('does not return response data', async () => {
      mockedClient.post.mockResolvedValue({
        data: {
          success: true,
          message: 'PID configuration updated',
        },
      } as any)

      const result = await setAreaPid('area1', true, false, ['home'])

      expect(result).toBeUndefined()
    })
  })

  describe('Integration with Other API Calls', () => {
    it('can be called multiple times for different areas', async () => {
      mockedClient.post.mockResolvedValue({ data: {} } as any)

      await setAreaPid('area1', true, true, ['schedule'])
      await setAreaPid('area2', false, false, ['home'])
      await setAreaPid('area3', true, false, ['comfort'])

      expect(mockedClient.post).toHaveBeenCalledTimes(3)
      expect(mockedClient.post).toHaveBeenNthCalledWith(1, '/areas/area1/pid', {
        enabled: true,
        automatic_gains: true,
        active_modes: ['schedule'],
      })
      expect(mockedClient.post).toHaveBeenNthCalledWith(2, '/areas/area2/pid', {
        enabled: false,
        automatic_gains: false,
        active_modes: ['home'],
      })
      expect(mockedClient.post).toHaveBeenNthCalledWith(3, '/areas/area3/pid', {
        enabled: true,
        automatic_gains: false,
        active_modes: ['comfort'],
      })
    })

    it('can be called sequentially with await', async () => {
      mockedClient.post.mockResolvedValue({ data: {} } as any)

      await setAreaPid('area1', true, true, ['schedule'])
      expect(mockedClient.post).toHaveBeenCalledTimes(1)

      await setAreaPid('area2', false, false, ['home'])
      expect(mockedClient.post).toHaveBeenCalledTimes(2)
    })

    it('can handle concurrent calls', async () => {
      mockedClient.post.mockResolvedValue({ data: {} } as any)

      await Promise.all([
        setAreaPid('area1', true, true, ['schedule']),
        setAreaPid('area2', true, false, ['home']),
        setAreaPid('area3', false, true, ['comfort']),
      ])

      expect(mockedClient.post).toHaveBeenCalledTimes(3)
    })
  })

  describe('Type Safety', () => {
    it('enforces boolean type for enabled parameter', async () => {
      mockedClient.post.mockResolvedValue({ data: {} } as any)

      // TypeScript should enforce boolean type
      await setAreaPid('area1', true, true, ['schedule'])
      await setAreaPid('area1', false, true, ['schedule'])

      // These would fail TypeScript compilation:
      // await setAreaPid('area1', 'true', true, ['schedule'])
      // await setAreaPid('area1', 1, true, ['schedule'])
    })

    it('enforces boolean type for automatic_gains parameter', async () => {
      mockedClient.post.mockResolvedValue({ data: {} } as any)

      await setAreaPid('area1', true, true, ['schedule'])
      await setAreaPid('area1', true, false, ['schedule'])

      // These would fail TypeScript compilation:
      // await setAreaPid('area1', true, 'false', ['schedule'])
      // await setAreaPid('area1', true, 0, ['schedule'])
    })

    it('enforces string array type for active_modes parameter', async () => {
      mockedClient.post.mockResolvedValue({ data: {} } as any)

      await setAreaPid('area1', true, true, ['schedule', 'home'])
      await setAreaPid('area1', true, true, [])

      // These would fail TypeScript compilation:
      // await setAreaPid('area1', true, true, 'schedule')
      // await setAreaPid('area1', true, true, [1, 2, 3])
      // await setAreaPid('area1', true, true, null)
    })
  })
})
