import React from 'react'
import { getDeviceStatus, getDeviceStatusIcon } from '../DeviceStatus'
import LocalFireDepartmentIcon from '@mui/icons-material/LocalFireDepartment'

describe('DeviceStatus helpers', () => {
  const area = { target_temperature: 22 } as any

  it('formats thermostat status with current and target', () => {
    const device = { type: 'thermostat', current_temperature: 20.5 }
    const res = getDeviceStatus(area, device)
    expect(res).toContain('20.5')
    expect(res).toContain('22.0')
  })

  it('returns temperature for temperature_sensor', () => {
    const device = { type: 'temperature_sensor', temperature: 19.2 }
    expect(getDeviceStatus(area, device)).toBe('19.2°C')
  })

  it('returns valve state and position', () => {
    const device = { type: 'valve', position: 50, state: 'open' }
    expect(getDeviceStatus(area, device)).toContain('50%')
    expect(getDeviceStatus(area, device)).toContain('open')
  })

  it('returns fire icon when thermostat should heat', () => {
    const device = { type: 'thermostat', current_temperature: 20 }
    const el = getDeviceStatusIcon(area, device) as any
    expect(el.type).toBe(LocalFireDepartmentIcon)
  })
})
