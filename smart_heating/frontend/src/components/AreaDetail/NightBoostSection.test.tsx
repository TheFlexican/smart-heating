import { describe, it, expect, vi, beforeEach } from 'vitest'
import { Zone } from '../../types'
import { NightBoostSection } from './NightBoostSection'

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

describe('NightBoostSection', () => {
  const mockArea: Zone = {
    id: 'living_room',
    name: 'Living Room',
    enabled: true,
    state: 'idle',
    target_temperature: 21,
    current_temperature: 20,
    devices: [],
    trv_entities: [],
    night_boost_enabled: true,
    night_boost_start_time: '22:00',
    night_boost_end_time: '06:00',
    night_boost_offset: 0.5,
    heating_type: 'radiator',
  }

  const mockT = (key: string, defaultValue?: string) => defaultValue || key

  const mockOnUpdate = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns a SettingSection with correct id', () => {
    const section = NightBoostSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.id).toBe('night-boost')
  })

  it('returns a SettingSection with correct title', () => {
    const section = NightBoostSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.title).toBe('settingsCards.nightBoostTitle')
  })

  it('shows ON badge when night boost is enabled', () => {
    const section = NightBoostSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.badge).toBe('ON')
  })

  it('shows OFF badge when night boost is disabled', () => {
    const disabledArea = { ...mockArea, night_boost_enabled: false }
    const section = NightBoostSection({
      area: disabledArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.badge).toBe('OFF')
  })

  it('shows disabled message for airco heating type', () => {
    const aircoArea = { ...mockArea, heating_type: 'airco' as const }
    const section = NightBoostSection({
      area: aircoArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.description).toBe('Disabled for Air Conditioner')
  })

  it('has defaultExpanded set to false', () => {
    const section = NightBoostSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.defaultExpanded).toBe(false)
  })

  it('includes content', () => {
    const section = NightBoostSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.content).toBeDefined()
  })
})
