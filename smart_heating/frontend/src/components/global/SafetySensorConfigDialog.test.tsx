import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, it, expect } from 'vitest'
import SafetySensorConfigDialog from './SafetySensorConfigDialog'

vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string) => k }) }))
vi.mock('../../api/config', () => ({ getBinarySensorEntities: vi.fn().mockResolvedValue([]) }))
import * as configApi from '../../api/config'

describe('SafetySensorConfigDialog', () => {
  it('renders info and shows no sensors when none found', async () => {
    const onAdd = vi.fn()
    const onClose = vi.fn()
    render(
      <SafetySensorConfigDialog
        open={true}
        onAdd={onAdd}
        onClose={onClose}
        configuredSensors={[]}
      />,
    )

    expect(await screen.findByTestId('safety-info')).toBeInTheDocument()
    // Open select and assert the 'no sensors' option is shown
    const select = await screen.findByTestId('safety-entity-select')
    await userEvent.click(select)
    expect(await screen.findByText('globalSettings.safety.noSensors')).toBeInTheDocument()
  })

  it('lists sensor entities and calls onAdd with selected config', async () => {
    vi.spyOn(configApi, 'getBinarySensorEntities').mockResolvedValueOnce([
      { entity_id: 'binary.smoke1', name: 'Smoke 1', attributes: { device_class: 'smoke' } },
    ])

    const onAdd = vi.fn().mockResolvedValue(undefined)
    const onClose = vi.fn()

    render(
      <SafetySensorConfigDialog
        open={true}
        onAdd={onAdd}
        onClose={onClose}
        configuredSensors={[]}
      />,
    )

    const select = await screen.findByTestId('safety-entity-select')
    await userEvent.click(select)

    const option = await screen.findByText('Smoke 1')
    await userEvent.click(option)

    // set attribute and alert value
    const attr = screen.getByTestId('safety-attribute-input') as HTMLInputElement
    await userEvent.clear(attr)
    await userEvent.type(attr, 'state')

    const alertVal = screen.getByTestId('safety-alert-value') as HTMLInputElement
    await userEvent.clear(alertVal)
    await userEvent.type(alertVal, 'detected')

    const addBtn = screen.getByTestId('safety-add-button')
    await userEvent.click(addBtn)

    expect(onAdd).toHaveBeenCalledWith({
      sensor_id: 'binary.smoke1',
      attribute: 'state',
      alert_value: 'detected',
      enabled: true,
    })
  })
})
