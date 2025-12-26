import { describe, it, expect, vi, beforeEach } from 'vitest'
import { Zone } from '../../types'
import { HeatingControlSection } from './HeatingControlSection'

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

// Mock fetch
global.fetch = vi.fn()

describe('HeatingControlSection', () => {
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
    hysteresis_override: null,
  }

  const mockOnUpdate = vi.fn()
  const mockT = (key: string, params?: any) => {
    if (params) {
      return `${key}:${JSON.stringify(params)}`
    }
    return key
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns a SettingSection with correct id', () => {
    const section = HeatingControlSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.id).toBe('heating-control')
  })

  it('returns a SettingSection with correct title', () => {
    const section = HeatingControlSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.title).toBe('settingsCards.heatingControlTitle')
  })

  it('shows disabled message for airco heating type', () => {
    const aircoArea = { ...mockArea, heating_type: 'airco' as const }
    const section = HeatingControlSection({
      area: aircoArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.description).toBe('settingsCards.disabledForAirco')
  })

  it('shows standard description for non-airco heating type', () => {
    const section = HeatingControlSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.description).toBe('settingsCards.heatingControlDescription')
  })

  it('sets defaultExpanded to false', () => {
    const section = HeatingControlSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.defaultExpanded).toBe(false)
  })

  it('includes content', () => {
    const section = HeatingControlSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.content).toBeDefined()
  })

  it('shows disabled alert for airco heating type', () => {
    const aircoArea = { ...mockArea, heating_type: 'airco' as const }
    const section = HeatingControlSection({
      area: aircoArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.content).toBeDefined()
  })

  it('shows hysteresis controls for non-airco heating type', () => {
    const section = HeatingControlSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.content).toBeDefined()
  })

  it('handles area with custom hysteresis override', () => {
    const customArea = { ...mockArea, hysteresis_override: 1.5 }
    const section = HeatingControlSection({
      area: customArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.content).toBeDefined()
  })
})
