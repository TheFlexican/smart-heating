import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { SafetySettings } from './SafetySettings'

const safetySensor = {
  alert_active: false,
  sensors: [{ sensor_id: 'sensor.smoke_1', attribute: 'smoke', enabled: true }],
}

describe('SafetySettings', () => {
  it('renders configured sensors and add button', () => {
    render(
      <SafetySettings
        safetySensor={safetySensor as any}
        onRemove={() => {}}
        onAddClick={() => {}}
      />,
    )

    expect(screen.getByTestId('safety-sensor-item')).toBeInTheDocument()
    expect(screen.getByTestId('global-add-safety-sensor')).toBeInTheDocument()
  })
})
