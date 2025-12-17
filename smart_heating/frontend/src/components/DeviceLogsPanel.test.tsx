import { render, screen, waitFor } from '@testing-library/react'
import { vi, it, expect } from 'vitest'
import DeviceLogsPanel from './DeviceLogsPanel'

vi.mock('../api/metrics', () => ({
  getAdvancedMetrics: vi.fn(),
}))

it('displays thermostat failure rows when metrics contain failures', async () => {
  const { getAdvancedMetrics } = require('../api/metrics')
  getAdvancedMetrics.mockResolvedValue({
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
