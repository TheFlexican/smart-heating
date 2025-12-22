import { render, screen, waitFor } from '@testing-library/react'
import { vi, it, expect, describe } from 'vitest'
import DeviceLogsPanel from './DeviceLogsPanel'

vi.mock('../api/metrics', () => ({
  getAdvancedMetrics: vi.fn(),
}))

describe('DeviceLogsPanel', () => {
  it('displays thermostat failure rows when metrics contain failures', async () => {
    vi.spyOn(await import('../../api/metrics'), 'getAdvancedMetrics').mockResolvedValue({
      metrics: [
        {
          timestamp: new Date().toISOString(),
          area_metrics: {
            living_room: {
              thermostat_failures: {
                'climate.t1': { count: 2, last_failure: 1234567890, retry_seconds: 120 },
              },
            },
          },
        },
      ],
    })

    render(<DeviceLogsPanel />)

    await waitFor(() => expect(screen.queryByText('living_room')).not.toBeNull())
    expect(screen.getByText('climate.t1')).toBeDefined()
    expect(screen.getByText('2')).toBeDefined()
  })

  it('shows live events when a device event is dispatched', async () => {
    // return a metrics array (length>0) so the component renders the metrics section
    vi.spyOn(await import('../../api/metrics'), 'getAdvancedMetrics').mockResolvedValue({
      metrics: [{}],
    })

    render(<DeviceLogsPanel />)

    // live events area should be present with "No live events yet"
    expect(await screen.findByText('No live events yet')).toBeInTheDocument()

    const evt = new CustomEvent('smart_heating.device_event', {
      detail: {
        timestamp: Date.now(),
        area_id: 'a1',
        device_id: 'd1',
        direction: 'in',
        action: 'test',
        payload: { ok: true },
      },
    })

    globalThis.dispatchEvent(evt)

    // now the live events table should show the device id
    expect(await screen.findByText('d1')).toBeInTheDocument()
  })
})
