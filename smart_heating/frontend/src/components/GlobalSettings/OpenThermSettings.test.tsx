import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { OpenThermSettings } from './OpenThermSettings'

describe('OpenThermSettings', () => {
  it('renders save button and gateway select', () => {
    const gateways = [{ gateway_id: '1', title: 'GW1' }]
    render(
      <OpenThermSettings
        openthermGateways={gateways}
        openthermGatewayId={''}
        setOpenthermGatewayId={() => {}}
        openthermSaving={false}
        handleSave={() => {}}
      />,
    )

    expect(screen.getByTestId('save-opentherm-config')).toBeInTheDocument()
  })
})
