import React from 'react'
import { render } from '@testing-library/react'
import PrimaryTemperatureSensor from './PrimaryTemperatureSensor'

const mockArea = { id: 'a1', devices: [], primary_temperature_sensor: null } as any

test('renders primary temperature sensor card', () => {
  const { container } = render(
    <PrimaryTemperatureSensor area={mockArea} loadData={async () => {}} />,
  )
  expect(container).toBeTruthy()
})
