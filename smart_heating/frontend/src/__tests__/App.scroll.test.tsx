import { render, screen, act } from '@testing-library/react'
import React from 'react'

// Mock useWebSocket to capture provided callbacks
let savedOpts: any = null
vi.mock('../hooks/useWebSocket', () => ({
  useWebSocket: (opts: any) => {
    savedOpts = opts
    return { metrics: {}, transportMode: 'websocket' }
  },
}))

// Mock backend APIs used during App initialization
vi.mock('../api/areas', () => ({ getZones: async () => [] }))
vi.mock('../api/devices', () => ({ getDevices: async () => [] }))
vi.mock('../api/config', () => ({ getConfig: async () => ({}) }))
vi.mock('../api/safety', () => ({ getSafetySensor: async () => ({ alert_active: false }) }))
vi.mock('../api/vacation', () => ({ getVacationMode: async () => ({ enabled: false }) }))

import App from '../App'

describe('App scroll preservation', () => {
  beforeEach(() => {
    // reset saved opts
    savedOpts = null
  })

  it('preserves scroll position when zones update arrives', async () => {
    // ensure Router basename matches rendered path
    window.history.pushState({}, 'Test page', '/smart_heating_ui/')

    // Mock backend API calls used during initial load
    vi.mock('../api/areas', () => ({ getZones: async () => [] }))
    vi.mock('../api/devices', () => ({ getDevices: async () => [] }))
    vi.mock('../api/config', () => ({ getConfig: async () => ({}) }))
    vi.mock('../api/safety', () => ({ getSafetySensor: async () => ({ alert_active: false }) }))

    render(<App />)

    const container = (await screen.findByTestId('zones-scroll-container')) as HTMLDivElement

    // simulate prior scroll
    Object.defineProperty(container, 'scrollTop', { value: 123, writable: true })
    container.scrollTop = 123

    // Prepare updated zones payload
    const updatedZones = [
      { id: 'a', name: 'A', devices: [], hidden: false, target_temperature: 20 },
    ]

    // Ensure our mock received options
    expect(savedOpts).not.toBeNull()
    // Call onZonesUpdate as if WebSocket delivered an update
    await act(async () => {
      await savedOpts.onZonesUpdate(updatedZones)
    })

    // Expect scrollTop restored
    expect(container.scrollTop).toBe(123)
  })
})
