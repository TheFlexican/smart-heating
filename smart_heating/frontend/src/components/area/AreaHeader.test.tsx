import React from 'react'
import { render, screen } from '@testing-library/react'
import AreaHeader from './AreaHeader'

const mockArea = {
  id: 'zone1',
  name: 'Living Room',
  state: 'idle',
  devices: [],
} as any

test('renders area name and enable switch', () => {
  render(
    <AreaHeader
      area={mockArea}
      enabled={true}
      onToggle={() => {}}
      onBack={() => {}}
      getStateColor={() => 'default'}
    />,
  )
  expect(screen.getByText('Living Room')).toBeInTheDocument()
  expect(screen.getByTestId('area-enable-switch')).toBeInTheDocument()
})
