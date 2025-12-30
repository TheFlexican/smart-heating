import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import EfficiencyReports from './EfficiencyReports'
import * as efficiencyApi from '../api/efficiency'
import userEvent from '@testing-library/user-event'

describe('EfficiencyReports', () => {
  test('renders recommendation items after area select', async () => {
    const user = userEvent.setup()

    vi.spyOn(efficiencyApi, 'getAllAreasEfficiency').mockResolvedValue({
      area_reports: [
        {
          area_id: 'a1',
          area_name: 'Area 1',
          metrics: {
            energy_score: 50,
            heating_time_percentage: 10,
            heating_cycles: 2,
            avg_temp_delta: 0,
          },
        },
      ],
      recommendations: [],
    } as any)

    vi.spyOn(efficiencyApi, 'getEfficiencyReport').mockResolvedValue({
      recommendations: ['rec1', 'rec2'],
      metrics: {
        energy_score: 50,
        heating_time_percentage: 10,
        heating_cycles: 2,
        avg_temp_delta: 0,
      },
    } as any)

    render(
      <MemoryRouter>
        <EfficiencyReports />
      </MemoryRouter>,
    )

    // Click the area row to load area report
    await waitFor(() => expect(screen.getByText('Area 1')).toBeInTheDocument())
    await user.click(screen.getByText('Area 1'))

    // Wait for recommendations to appear
    await waitFor(() => expect(screen.getByText('rec1')).toBeInTheDocument())
    expect(screen.getByText('rec2')).toBeInTheDocument()
  })

  test('renders global recommendations when no area selected', async () => {
    vi.spyOn(efficiencyApi, 'getAllAreasEfficiency').mockResolvedValue({
      area_reports: [],
      recommendations: ['global-rec'],
    } as any)

    render(
      <MemoryRouter>
        <EfficiencyReports />
      </MemoryRouter>,
    )

    await waitFor(() => expect(screen.getByText('global-rec')).toBeInTheDocument())
  })
})
