import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import HistoryChart from './HistoryChart'
import * as api from '../../api/history'
import { vi } from 'vitest'

// Mock translation
vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string) => k }) }))

it('shows cooling series when history contains cooling state', async () => {
  const now = new Date().toISOString()
  const older = new Date(Date.now() - 1000 * 60 * 30).toISOString() // 30m older
  vi.spyOn(api, 'getHistory').mockResolvedValue({
    entries: [
      { timestamp: now, current_temperature: 22, target_temperature: 21, state: 'cooling' },
      { timestamp: older, current_temperature: 21.5, target_temperature: 21, state: 'idle' },
    ],
  })

  render(<HistoryChart areaId="a1" />)

  // Ensure data is sorted so the latest timestamp (now) is the last point
  await waitFor(() => expect(screen.getByTestId('history-chart')).toBeInTheDocument())
  // The hidden indicator should reflect cooling
  await waitFor(() => expect(screen.getByTestId('history-has-cooling').textContent).toBe('1'))

  // Continue cooling-series assertions for this test

  // Wait for chart to render data and indicate cooling presence
  await waitFor(() => expect(screen.getByTestId('history-has-cooling').textContent).toBe('1'))

  // Chart container should be present
  expect(screen.getByTestId('history-chart')).toBeInTheDocument()

  // Toggles for cooling should be present
  expect(screen.getByTestId('history-toggle-cooling')).toBeInTheDocument()

  // Legend items should render with testids (use the descriptive legend list)
  await waitFor(() => expect(screen.getByTestId('history-legend-item-temp')).toBeInTheDocument())
  await waitFor(() => expect(screen.getByTestId('history-legend-item-target')).toBeInTheDocument())
  // Legend should include either heating (red dots) or cooling (blue dots)
  await waitFor(() =>
    expect(
      screen.queryByTestId('history-legend-item-redDots') ||
        screen.queryByTestId('history-legend-item-blueDots'),
    ).toBeInTheDocument(),
  )

  // Cooling toggle should be present
  await waitFor(() => expect(screen.getByTestId('history-toggle-cooling')).toBeInTheDocument())
})

it('renders TRV position series and toggle when history contains trv entries', async () => {
  vi.restoreAllMocks()
  const now = new Date().toISOString()
  vi.spyOn(api, 'getHistory').mockResolvedValue({
    entries: [
      {
        timestamp: now,
        current_temperature: 22,
        target_temperature: 21,
        state: 'idle',
        trvs: [{ entity_id: 'sensor.trv_pos', position: 45, open: true }],
      },
    ],
  })

  render(<HistoryChart areaId="a1" />)

  await waitFor(() => expect(screen.getByTestId('history-chart')).toBeInTheDocument())

  // TRV toggle should be present
  await waitFor(() => expect(screen.getByTestId('history-toggle-trvs')).toBeInTheDocument())

  // Ensure TRV ids were detected and exposed for testing
  await waitFor(() =>
    expect(screen.getByTestId('history-trv-ids').textContent).toContain('sensor.trv_pos'),
  )
})

it('defaults to 4h selector and exposes range buttons', async () => {
  // Reset mocks and set up a simple idle history
  vi.restoreAllMocks()
  const now = new Date().toISOString()
  vi.spyOn(api, 'getHistory').mockResolvedValue({
    entries: [{ timestamp: now, current_temperature: 22, target_temperature: 21, state: 'idle' }],
  })

  render(<HistoryChart areaId="a1" />)

  // Check selector buttons exist (wait for loading to finish)
  await waitFor(() => {
    expect(screen.getByTestId('history-range-1h')).toBeInTheDocument()
    expect(screen.getByTestId('history-range-2h')).toBeInTheDocument()
    expect(screen.getByTestId('history-range-4h')).toBeInTheDocument()
    expect(screen.getByTestId('history-range-8h')).toBeInTheDocument()
    expect(screen.getByTestId('history-range-24h')).toBeInTheDocument()
    expect(screen.getByTestId('history-range-custom')).toBeInTheDocument()

    // The 4h button should be selected by default (aria-pressed === true)
    expect(screen.getByTestId('history-range-4h').getAttribute('aria-pressed')).toBe('true')
  })

  // Additional basic smoke checks to ensure chart renders
  await waitFor(() => expect(screen.getByTestId('history-chart')).toBeInTheDocument())
})
