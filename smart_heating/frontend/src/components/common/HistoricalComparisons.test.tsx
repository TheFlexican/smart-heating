import React from 'react'
import { render, screen } from '@testing-library/react'
import { vi, describe, it, expect } from 'vitest'
import HistoricalComparisons from './HistoricalComparisons'

vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string) => k }) }))
vi.mock('react-router-dom', () => ({ useNavigate: () => vi.fn() }))
vi.mock('../../api/efficiency', () => ({ getComparison: vi.fn(), getCustomComparison: vi.fn() }))
import * as api from '../../api/efficiency'

describe('HistoricalComparisons', () => {
  it('renders summary and table when comparison data provided', async () => {
    const sample = {
      summary_delta: {
        energy_score: { is_improvement: true, change: 5, percent_change: 6 },
        heating_time: { is_improvement: false, change: -2, percent_change: -10 },
        heating_cycles: { is_improvement: false, change: 0, percent_change: 0 },
        temp_delta: { is_improvement: false, change: 0, percent_change: 0 },
      },
      current_summary: {
        energy_score: 80,
        heating_time_percentage: 20,
        heating_cycles: 10,
        avg_temp_delta: 0.5,
      },
      previous_summary: {
        energy_score: 75,
        heating_time_percentage: 25,
        heating_cycles: 12,
        avg_temp_delta: 0.6,
      },
      area_comparisons: [
        {
          area_id: 'a1',
          area_name: 'Area 1',
          current_metrics: { energy_score: 80, heating_time_percentage: 20, heating_cycles: 10 },
          deltas: {
            energy_score: { is_improvement: true, change: 1, percent_change: 1 },
            heating_time: { is_improvement: false, change: -2, percent_change: -10 },
            heating_cycles: { is_improvement: false, change: 0, percent_change: 0 },
          },
        },
      ],
    }

    vi.spyOn(api, 'getComparison').mockResolvedValue(sample)

    render(<HistoricalComparisons />)

    expect(await screen.findByText('comparison.title')).toBeInTheDocument()
    expect(await screen.findByText('comparison.summary')).toBeInTheDocument()
    expect(await screen.findByText('Area 1')).toBeInTheDocument()
  })
})
