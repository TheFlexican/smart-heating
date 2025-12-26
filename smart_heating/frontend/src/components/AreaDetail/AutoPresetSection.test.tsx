import { describe, it, expect, vi, beforeEach } from 'vitest'
import { Zone } from '../../types'
import { AutoPresetSection } from './AutoPresetSection'

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

describe('AutoPresetSection', () => {
  const mockArea: Zone = {
    id: 'living_room',
    name: 'Living Room',
    enabled: true,
    state: 'idle',
    target_temperature: 21,
    current_temperature: 20,
    devices: [],
    trv_entities: [],
    auto_preset_enabled: true,
    auto_preset_home: 'home',
    auto_preset_away: 'away',
    presence_sensors: ['binary_sensor.living_room_motion'],
  }

  const mockT = (key: string) => key

  const mockOnUpdate = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns a SettingSection with correct id', () => {
    const section = AutoPresetSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.id).toBe('auto-preset')
  })

  it('returns a SettingSection with correct title', () => {
    const section = AutoPresetSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.title).toBe('settingsCards.autoPresetTitle')
  })

  it('shows AUTO badge when auto preset is enabled', () => {
    const section = AutoPresetSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.badge).toBe('AUTO')
  })

  it('shows OFF badge when auto preset is disabled', () => {
    const disabledArea = { ...mockArea, auto_preset_enabled: false }
    const section = AutoPresetSection({
      area: disabledArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.badge).toBe('OFF')
  })

  it('has defaultExpanded set to false', () => {
    const section = AutoPresetSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.defaultExpanded).toBe(false)
  })

  it('includes content', () => {
    const section = AutoPresetSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.content).toBeDefined()
  })
})
