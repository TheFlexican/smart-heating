import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, it, expect } from 'vitest'

vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string) => k }) }))
vi.mock('../../api/sensors', () => ({
  addWindowSensor: vi.fn().mockResolvedValue(undefined),
  addPresenceSensor: vi.fn().mockResolvedValue(undefined),
  removeWindowSensor: vi.fn().mockResolvedValue(undefined),
  removePresenceSensor: vi.fn().mockResolvedValue(undefined),
}))
import * as sensorsApi from '../../api/sensors'

// Mock SensorConfigDialog to simulate add flow
vi.mock('./SensorConfigDialog', () => ({
  __esModule: true,
  default: ({ open, onClose, onAdd }: any) =>
    open ? (
      <div>
        <button data-testid="sensor-save" onClick={() => onAdd({ entity_id: 'sensor.new' })}>
          Save
        </button>
        <button data-testid="sensor-close" onClick={onClose}>
          Close
        </button>
      </div>
    ) : null,
}))

import SensorConfigControls from './SensorConfigControls'

describe('SensorConfigControls', () => {
  it('shows no sensors and can add presence sensor', async () => {
    const area = { id: 'a1', window_sensors: [], presence_sensors: [] }
    const loadData = vi.fn().mockResolvedValue(undefined)
    render(<SensorConfigControls area={area as any} entityStates={{}} loadData={loadData} />)

    const addPresence = screen.getByTestId('add-presence-sensor-button')
    await userEvent.click(addPresence)

    // dialog should appear and save then call API
    const save = await screen.findByTestId('sensor-save')
    await userEvent.click(save)

    expect(sensorsApi.addPresenceSensor).toHaveBeenCalledWith(area.id, { entity_id: 'sensor.new' })
    expect(loadData).toHaveBeenCalled()
  })

  it('removes window sensor', async () => {
    const area = { id: 'a2', window_sensors: ['binary.win1'], presence_sensors: [] }
    const loadData = vi.fn().mockResolvedValue(undefined)
    render(<SensorConfigControls area={area as any} entityStates={{}} loadData={loadData} />)

    const item = screen.getByTestId('window-sensor-item')
    const removeBtn = item.querySelector('button')
    if (removeBtn) await userEvent.click(removeBtn)

    expect(sensorsApi.removeWindowSensor).toHaveBeenCalledWith(area.id, 'binary.win1')
    expect(loadData).toHaveBeenCalled()
  })
})
