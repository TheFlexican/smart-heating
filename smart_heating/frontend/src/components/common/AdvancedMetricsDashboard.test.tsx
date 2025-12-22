import React from 'react'
import { render } from '@testing-library/react'
import AdvancedMetricsDashboard from './AdvancedMetricsDashboard'
import { MemoryRouter } from 'react-router-dom'

test('renders AdvancedMetricsDashboard', () => {
  const { container } = render(
    <MemoryRouter>
      <AdvancedMetricsDashboard />
    </MemoryRouter>,
  )
  expect(container).toBeTruthy()
})
