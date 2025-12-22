import React from 'react'
import { render, screen } from '@testing-library/react'
import DeviceOverview from './DeviceOverview'

test('renders DeviceOverview empty state', () => {
  render(<DeviceOverview areas={[]} />)
  expect(screen.getByText(/Device Overview/i)).toBeInTheDocument()
})
