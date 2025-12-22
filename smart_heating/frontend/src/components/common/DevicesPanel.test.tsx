import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import DevicesPanel from './DevicesPanel'
import { vi, describe, it, expect } from 'vitest'

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (k: string, v?: any) => (v && v.count !== undefined ? `${v.count}` : k),
  }),
}))

describe('DevicesPanel', () => {
  const make = (overrides: any = {}) => {
    const area = {
      id: 'a1',
      name: 'Room',
      devices: overrides.devices ?? [],
      target_temperature: 22,
      heating_type: overrides.heating_type,
    }

    const availableDevices = overrides.availableDevices ?? []
    const loadData = vi.fn().mockResolvedValue(undefined)
    const addDeviceToZone = vi.fn().mockResolvedValue(undefined)
    const removeDeviceFromZone = vi.fn().mockResolvedValue(undefined)
    const getDeviceStatusIcon = (device: any) => <span data-testid={`icon-${device.id}`}>I</span>
    const getDeviceStatus = (device: any) => 'ok'

    return {
      area,
      availableDevices,
      loadData,
      addDeviceToZone,
      removeDeviceFromZone,
      getDeviceStatusIcon,
      getDeviceStatus,
    }
  }

  it('renders assigned devices and remove triggers API + load', async () => {
    const cfg = make({ devices: [{ id: 'd1', name: 'T1', entity_id: 'climate.t1' }] })
    render(
      <DevicesPanel
        area={cfg.area as any}
        availableDevices={cfg.availableDevices as any}
        loadData={cfg.loadData}
        addDeviceToZone={cfg.addDeviceToZone}
        removeDeviceFromZone={cfg.removeDeviceFromZone}
        getDeviceStatusIcon={cfg.getDeviceStatusIcon}
        getDeviceStatus={cfg.getDeviceStatus}
      />,
    )

    const removeBtn = screen.getByTestId('remove-device-climate.t1')
    await userEvent.click(removeBtn)

    expect(cfg.removeDeviceFromZone).toHaveBeenCalledWith(cfg.area.id, 'climate.t1')
    expect(cfg.loadData).toHaveBeenCalled()
  })

  it('adds available device and disables valve when airco', async () => {
    const availableDevices = [
      {
        id: 'd2',
        name: 'Thermostat',
        type: 'thermostat',
        subtype: 'climate',
        entity_id: 'climate.t2',
      },
      { id: 'v1', name: 'Valve', type: 'valve', subtype: 'valve', entity_id: 'switch.v1' },
    ]

    const cfg = make({ availableDevices, heating_type: 'airco' })
    // set area heating_type to airco
    cfg.area.heating_type = 'airco'

    render(
      <DevicesPanel
        area={cfg.area as any}
        availableDevices={cfg.availableDevices as any}
        loadData={cfg.loadData}
        addDeviceToZone={cfg.addDeviceToZone}
        removeDeviceFromZone={cfg.removeDeviceFromZone}
        getDeviceStatusIcon={cfg.getDeviceStatusIcon}
        getDeviceStatus={cfg.getDeviceStatus}
      />,
    )

    const addThermostat = screen.getByTestId('add-available-device-climate.t2')
    await userEvent.click(addThermostat)
    expect(cfg.addDeviceToZone).toHaveBeenCalledWith(
      cfg.area.id,
      expect.objectContaining({ device_id: 'climate.t2' }),
    )
    expect(cfg.loadData).toHaveBeenCalled()

    // Need to disable 'showOnlyHeating' to make valve appear in list
    const toggle = screen.getByLabelText('areaDetail.showOnlyClimate') as HTMLInputElement
    await userEvent.click(toggle)

    const addValve = screen.getByTestId('add-available-device-switch.v1')
    expect(addValve).toBeDisabled()
  })

  it('filters available devices via search', async () => {
    const availableDevices = [
      {
        id: 'd2',
        name: 'Thermostat',
        type: 'thermostat',
        subtype: 'climate',
        entity_id: 'climate.t2',
      },
      {
        id: 'd3',
        name: 'Sensor',
        type: 'temperature_sensor',
        subtype: 'temperature',
        entity_id: 'sensor.s1',
      },
    ]
    const cfg = make({ availableDevices })
    render(
      <DevicesPanel
        area={cfg.area as any}
        availableDevices={cfg.availableDevices as any}
        loadData={cfg.loadData}
        addDeviceToZone={cfg.addDeviceToZone}
        removeDeviceFromZone={cfg.removeDeviceFromZone}
        getDeviceStatusIcon={cfg.getDeviceStatusIcon}
        getDeviceStatus={cfg.getDeviceStatus}
      />,
    )

    const input = screen.getByPlaceholderText('areaDetail.searchPlaceholder') as HTMLInputElement
    await userEvent.type(input, 'Thermostat')

    expect(screen.queryByTestId('add-available-device-climate.t2')).toBeInTheDocument()
    expect(screen.queryByTestId('add-available-device-sensor.s1')).toBeNull()
  })

  it('toggle showOnlyHeating affects available devices count', async () => {
    const availableDevices = [
      {
        id: 'd2',
        name: 'Thermostat',
        type: 'thermostat',
        subtype: 'climate',
        entity_id: 'climate.t2',
      },
      { id: 'd3', name: 'Other', type: 'other', subtype: 'other', entity_id: 'other.o1' },
    ]
    const cfg = make({ availableDevices })
    render(
      <DevicesPanel
        area={cfg.area as any}
        availableDevices={cfg.availableDevices as any}
        loadData={cfg.loadData}
        addDeviceToZone={cfg.addDeviceToZone}
        removeDeviceFromZone={cfg.removeDeviceFromZone}
        getDeviceStatusIcon={cfg.getDeviceStatusIcon}
        getDeviceStatus={cfg.getDeviceStatus}
      />,
    )

    // initially showOnlyHeating true, only 1 matching
    const addButtonsInitially = screen.getAllByTestId(/add-available-device-/)
    expect(addButtonsInitially.length).toBe(1)

    const toggle = screen.getByLabelText('areaDetail.showOnlyClimate') as HTMLInputElement
    await userEvent.click(toggle)

    const addButtonsAfter = screen.getAllByTestId(/add-available-device-/)
    expect(addButtonsAfter.length).toBe(2)
  })
})
