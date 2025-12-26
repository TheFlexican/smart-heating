import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { SensorsSettings } from './SensorsSettings'

const presenceSensors = [
  { entity_id: 'binary_sensor.presence_1' },
  { entity_id: 'binary_sensor.presence_2' },
]

describe('SensorsSettings', () => {
  it('renders sensors and add button', () => {
    render(
      <SensorsSettings
        presenceSensors={presenceSensors as any}
        onRemove={() => {}}
        onAddClick={() => {}}
      />,
    )

    expect(screen.getAllByTestId('presence-sensor-item').length).toBeGreaterThan(0)
    expect(screen.getByTestId('global-add-presence-sensor')).toBeInTheDocument()
  })
})
