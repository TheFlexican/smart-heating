import { describe, it, expect, vi, beforeEach } from 'vitest'
import { Zone } from '../../types'
import { WindowSensorsSection } from './WindowSensorsSection'

// Mock the API functions
vi.mock('../../api/sensors', () => ({
  removeWindowSensor: vi.fn(),
}))

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, params?: any) => {
      if (params) {
        return `${key}:${JSON.stringify(params)}`
      }
      return key
    },
  }),
}))

describe('WindowSensorsSection', () => {
  const mockArea: Zone = {
    id: 'living_room',
    name: 'Living Room',
    enabled: true,
    state: 'idle',
    preset_mode: 'comfort',
    target_temperature: 21,
    current_temperature: 20,
    devices: [],
    trv_entities: [],
    window_sensors: [],
  }

  const mockOnUpdate = vi.fn()
  const mockOnOpenAddDialog = vi.fn()
  const mockT = (key: string) => key

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns a SettingSection with correct id', () => {
    const section = WindowSensorsSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      onOpenAddDialog: mockOnOpenAddDialog,
      t: mockT,
    })

    expect(section.id).toBe('window-sensors')
  })

  it('returns a SettingSection with correct title', () => {
    const section = WindowSensorsSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      onOpenAddDialog: mockOnOpenAddDialog,
      t: mockT,
    })

    expect(section.title).toBe('settingsCards.windowSensorsTitle')
  })

  it('shows badge with sensor count when sensors exist', () => {
    const areaWithSensors = {
      ...mockArea,
      window_sensors: [
        { entity_id: 'binary_sensor.window_1', action_when_open: 'turn_off', temp_drop: 0 },
        {
          entity_id: 'binary_sensor.window_2',
          action_when_open: 'reduce_temperature',
          temp_drop: 5,
        },
      ],
    }
    const section = WindowSensorsSection({
      area: areaWithSensors,
      onUpdate: mockOnUpdate,
      onOpenAddDialog: mockOnOpenAddDialog,
      t: mockT,
    })

    expect(section.badge).toBe(2)
  })

  it('does not show badge when no sensors', () => {
    const section = WindowSensorsSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      onOpenAddDialog: mockOnOpenAddDialog,
      t: mockT,
    })

    expect(section.badge).toBeUndefined()
  })

  it('sets defaultExpanded to false', () => {
    const section = WindowSensorsSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      onOpenAddDialog: mockOnOpenAddDialog,
      t: mockT,
    })

    expect(section.defaultExpanded).toBe(false)
  })

  it('includes content', () => {
    const section = WindowSensorsSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      onOpenAddDialog: mockOnOpenAddDialog,
      t: mockT,
    })

    expect(section.content).toBeDefined()
  })
})
