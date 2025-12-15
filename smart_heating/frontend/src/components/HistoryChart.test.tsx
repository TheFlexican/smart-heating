/// <reference types="vitest" />
import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import HistoryChart from './HistoryChart'
import * as api from '../api/history'
import { vi } from 'vitest'

// Mock translation
vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string) => k }) }))

it('shows cooling series when history contains cooling state', async () => {
  const now = new Date().toISOString()
  vi.spyOn(api, 'getHistory').mockResolvedValue({ entries: [
    { timestamp: now, current_temperature: 22, target_temperature: 21, state: 'cooling' }
  ] })

  render(<HistoryChart areaId="a1" />)

  // Wait for chart to render data and indicate cooling presence
  await waitFor(() => expect(screen.getByTestId('history-has-cooling').textContent).toBe('1'))
})
