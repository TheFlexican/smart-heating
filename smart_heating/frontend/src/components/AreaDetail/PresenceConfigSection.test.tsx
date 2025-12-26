import { describe, it, expect, vi, beforeEach } from 'vitest'
import { Zone } from '../../types'
import { PresenceConfigSection } from './PresenceConfigSection'

// Mock the API functions
vi.mock('../../api/sensors', () => ({
  setAreaPresenceConfig: vi.fn(),
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

describe('PresenceConfigSection', () => {
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
    use_global_presence: false,
  }

  const mockOnUpdate = vi.fn()
  const mockT = (key: string) => key

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns a SettingSection with correct id', () => {
    const section = PresenceConfigSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.id).toBe('presence-config')
  })

  it('returns a SettingSection with correct title', () => {
    const section = PresenceConfigSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.title).toBe('settingsCards.presenceConfigTitle')
  })

  it('sets defaultExpanded to false', () => {
    const section = PresenceConfigSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.defaultExpanded).toBe(false)
  })

  it('includes content', () => {
    const section = PresenceConfigSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.content).toBeDefined()
  })
})
