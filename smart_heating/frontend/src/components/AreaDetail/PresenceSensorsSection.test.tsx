import { describe, it, expect, vi, beforeEach } from 'vitest'
import { Zone } from '../../types'
import { PresenceSensorsSection } from './PresenceSensorsSection'

// Mock the API functions
vi.mock('../../api/sensors', () => ({
  removePresenceSensor: vi.fn(),
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

describe('PresenceSensorsSection', () => {
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
    presence_sensors: [],
  }

  const mockEntityStates = {}
  const mockOnUpdate = vi.fn()
  const mockOnOpenAddDialog = vi.fn()
  const mockT = (key: string) => key

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns a SettingSection with correct id', () => {
    const section = PresenceSensorsSection({
      area: mockArea,
      entityStates: mockEntityStates,
      onUpdate: mockOnUpdate,
      onOpenAddDialog: mockOnOpenAddDialog,
      t: mockT,
    })

    expect(section.id).toBe('presence-sensors')
  })

  it('returns a SettingSection with correct title', () => {
    const section = PresenceSensorsSection({
      area: mockArea,
      entityStates: mockEntityStates,
      onUpdate: mockOnUpdate,
      onOpenAddDialog: mockOnOpenAddDialog,
      t: mockT,
    })

    expect(section.title).toBe('settingsCards.presenceSensorsTitle')
  })

  it('shows badge with sensor count when sensors exist', () => {
    const areaWithSensors = {
      ...mockArea,
      presence_sensors: [
        { entity_id: 'person.john', inverted: false },
        { entity_id: 'person.jane', inverted: false },
      ],
    }
    const section = PresenceSensorsSection({
      area: areaWithSensors,
      entityStates: mockEntityStates,
      onUpdate: mockOnUpdate,
      onOpenAddDialog: mockOnOpenAddDialog,
      t: mockT,
    })

    expect(section.badge).toBe(2)
  })

  it('does not show badge when no sensors', () => {
    const section = PresenceSensorsSection({
      area: mockArea,
      entityStates: mockEntityStates,
      onUpdate: mockOnUpdate,
      onOpenAddDialog: mockOnOpenAddDialog,
      t: mockT,
    })

    expect(section.badge).toBeUndefined()
  })

  it('sets defaultExpanded to false', () => {
    const section = PresenceSensorsSection({
      area: mockArea,
      entityStates: mockEntityStates,
      onUpdate: mockOnUpdate,
      onOpenAddDialog: mockOnOpenAddDialog,
      t: mockT,
    })

    expect(section.defaultExpanded).toBe(false)
  })

  it('includes content', () => {
    const section = PresenceSensorsSection({
      area: mockArea,
      entityStates: mockEntityStates,
      onUpdate: mockOnUpdate,
      onOpenAddDialog: mockOnOpenAddDialog,
      t: mockT,
    })

    expect(section.content).toBeDefined()
  })
})
