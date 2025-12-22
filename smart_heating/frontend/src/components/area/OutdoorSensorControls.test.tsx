import React from 'react'
import { render, screen } from '@testing-library/react'
import { vi, describe, it, expect } from 'vitest'

vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string) => k }) }))
vi.mock('../../api/config', () => ({
  getWeatherEntities: vi.fn().mockResolvedValue([]),
  getEntityState: vi.fn(),
}))
import OutdoorSensorControls from './OutdoorSensorControls'

const area = { id: 'area1', smart_boost_enabled: true, weather_entity_id: '' } as any

describe('OutdoorSensorControls', () => {
  it('renders select and helper text', () => {
    render(<OutdoorSensorControls area={area} loadData={async () => {}} />)

    // helper text is unique
    expect(screen.getByText('settingsCards.outdoorTemperatureSensorHelper')).toBeInTheDocument()
    // there should be a combobox/select element
    expect(screen.getByRole('combobox')).toBeInTheDocument()
  })
})
