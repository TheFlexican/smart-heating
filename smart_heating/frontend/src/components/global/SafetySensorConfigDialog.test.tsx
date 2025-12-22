import React from 'react'
import { render, screen, within } from '@testing-library/react'
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

    // use the hidden native select to set the value reliably in tests
    const native = await screen.findByTestId('safety-entity-native')
    import('@testing-library/dom').then(({ fireEvent }) => {
      fireEvent.change(native, { target: { value: 'binary.smoke1' } })
    })

    // set attribute and alert value (find input inside TextField wrapper)
    const attrWrapper = screen.getByTestId('safety-attribute-input')
    const attrInput = within(attrWrapper).getByRole('textbox')
    await userEvent.clear(attrInput)
    await userEvent.type(attrInput, 'state')

    const alertWrapper = screen.getByTestId('safety-alert-value')
    const alertInput = within(alertWrapper).getByRole('textbox')
    await userEvent.clear(alertInput)
    await userEvent.type(alertInput, 'detected')

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
