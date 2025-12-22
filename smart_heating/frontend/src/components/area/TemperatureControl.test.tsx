import React from 'react'
import { render, screen } from '@testing-library/react'
import TemperatureControl from './TemperatureControl'

const mockArea = {
  id: 'zone1',
  current_temperature: 19.3,
  preset_mode: 'none',
} as any

test('renders target temperature and current temperature', () => {
  render(
    <TemperatureControl
      area={mockArea}
      temperature={21}
      enabled={true}
      onTemperatureChange={() => {}}
      onTemperatureCommit={async () => {}}
      onOpenTrvDialog={() => {}}
      trvs={[]}
      loadData={async () => {}}
    />,
  )

  expect(screen.getByText('21°C')).toBeInTheDocument()
  expect(screen.getByText('19.3°C')).toBeInTheDocument()
})
