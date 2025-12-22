import React from 'react'
import { render, screen } from '@testing-library/react'
import ZoneList from './ZoneList'
import { MemoryRouter } from 'react-router-dom'

const areas = [{ id: 'z1', name: 'Zone 1', devices: [], hidden: false, target_temperature: 20 }]

test('renders ZoneList with areas', () => {
  render(
    <MemoryRouter>
      <ZoneList
        areas={areas as any}
        loading={false}
        onUpdate={() => {}}
        showHidden={false}
        onToggleShowHidden={() => {}}
        onAreasReorder={() => {}}
      />
    </MemoryRouter>,
  )

  expect(screen.getByText(/Zone 1/i)).toBeInTheDocument()
})
