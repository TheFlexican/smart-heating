import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { AdvancedSettings } from './AdvancedSettings'

describe('AdvancedSettings', () => {
  it('renders theme and hysteresis sections', () => {
    render(
      <AdvancedSettings
        themeMode="light"
        onThemeChange={() => {}}
        hysteresis={0.5}
        saving={false}
        onHysteresisChange={() => {}}
        onHysteresisCommit={() => {}}
        onOpenHysteresisHelp={() => {}}
        hideDevicesPanel={false}
        onToggleHideDevicesPanel={() => {}}
        advancedControlEnabled={false}
        heatingCurveEnabled={false}
        pwmEnabled={false}
        pidEnabled={false}
        overshootProtectionEnabled={false}
        defaultCoefficient={1}
        onToggleAdvancedControl={() => {}}
        onResetAdvancedControl={() => {}}
        onRunCalibration={() => {}}
        calibrating={false}
        calibrationResult={null}
      />,
    )

    expect(screen.getByText('globalSettings.theme.title')).toBeInTheDocument()
    expect(screen.getByTestId('global-hysteresis-slider')).toBeInTheDocument()
  })
})
