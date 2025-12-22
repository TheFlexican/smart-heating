import React from 'react'
import { render, screen } from '@testing-library/react'
import TrvList from './TrvList'

const mockArea = {
  id: 'zone1',
  trv_entities: [{ entity_id: 'sensor.trv1', name: 'TRV 1', role: 'both' }],
  trvs: [{ entity_id: 'sensor.trv1', name: 'TRV 1', open: true, position: 42 }],
} as any

test('renders Add TRV button and TRV entries', () => {
  render(
    <TrvList area={mockArea} trvs={mockArea.trvs} onOpenAdd={() => {}} loadData={async () => {}} />,
  )

  // Add button present
  expect(screen.getByTestId('trv-add-button-overview')).toBeInTheDocument()

  // TRV entry rendered
  expect(screen.getByText('TRV 1')).toBeInTheDocument()
  expect(screen.getByTestId('trv-open-sensor.trv1')).toBeInTheDocument()
  expect(screen.getByTestId('trv-position-sensor.trv1')).toBeInTheDocument()
})
