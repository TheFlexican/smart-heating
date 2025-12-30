import React from 'react'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import ZoneCard from '../components/ZoneCard'

const area = {
  id: 'living_room',
  name: 'Living Room',
  enabled: true,
  state: 'heating',
  target_temperature: 21,
  effective_target_temperature: 22,
  boost_mode_active: false,
  manual_override: false,
  devices: [],
  presence_sensors: [],
}

test('renders zone card with name and target temperature', () => {
  render(
    <MemoryRouter>
      <ZoneCard area={area as any} onUpdate={() => {}} />
    </MemoryRouter>,
  )

  expect(screen.getByText(/Living Room/)).toBeInTheDocument()
  expect(screen.getByTestId('target-temperature-display')).toBeInTheDocument()
})
