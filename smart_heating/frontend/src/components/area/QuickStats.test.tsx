import React from 'react'
import { render, screen } from '@testing-library/react'
import QuickStats from './QuickStats'

const mockArea = {
  id: 'zone1',
  devices: [{ id: 'd1' }],
  state: 'heating',
} as any

test('renders quick stats with device count, state and id', () => {
  render(<QuickStats area={mockArea} />)

  expect(screen.getByText('1')).toBeTruthy()
  expect(screen.getByText('heating')).toBeTruthy()
  expect(screen.getByText('zone1')).toBeTruthy()
})
