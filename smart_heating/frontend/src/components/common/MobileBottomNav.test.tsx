import React from 'react'
import { render } from '@testing-library/react'
import MobileBottomNav from './MobileBottomNav'
import { MemoryRouter } from 'react-router-dom'

test('renders MobileBottomNav', () => {
  const { container } = render(
    <MemoryRouter>
      <MobileBottomNav />
    </MemoryRouter>,
  )
  expect(container).toBeTruthy()
})
