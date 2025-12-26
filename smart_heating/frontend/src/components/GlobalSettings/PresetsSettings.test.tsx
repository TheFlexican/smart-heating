import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { PresetsSettings } from './PresetsSettings'

const mockPresets = {
  away_temp: 10,
  eco_temp: 15,
  comfort_temp: 21,
  home_temp: 20,
  sleep_temp: 17,
  activity_temp: 22,
}

describe('PresetsSettings', () => {
  it('renders labels and sliders', () => {
    render(
      <PresetsSettings
        presets={mockPresets}
        saving={false}
        onChange={() => {}}
        onCommit={() => {}}
      />,
    )

    // i18n in tests returns the translation key by default
    expect(screen.getByText('globalSettings.presets.title')).toBeInTheDocument()
    expect(screen.getByTestId('global-preset-away-slider')).toBeInTheDocument()
    expect(screen.getByTestId('global-preset-comfort-slider')).toBeInTheDocument()
  })
})
