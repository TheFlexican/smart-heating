import React from 'react'
import { render } from '@testing-library/react'
import EfficiencyReports from './EfficiencyReports'
import { MemoryRouter } from 'react-router-dom'

test('renders EfficiencyReports header', () => {
  const { container } = render(
    <MemoryRouter>
      <EfficiencyReports />
    </MemoryRouter>,
  )
  expect(container).toBeTruthy()
})
