import { describe, it, expect, vi, beforeEach } from 'vitest'
import { Zone, HassEntity } from '../../types'
import { SmartNightBoostSection } from './SmartNightBoostSection'

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

describe('SmartNightBoostSection', () => {
  const mockArea: Zone = {
    id: 'living_room',
    name: 'Living Room',
    enabled: true,
    state: 'idle',
    target_temperature: 21,
    current_temperature: 20,
    devices: [],
    trv_entities: [],
    smart_boost_enabled: true,
    smart_boost_target_time: '06:00',
    weather_entity_id: 'sensor.outdoor_temperature',
    heating_type: 'radiator',
  }

  const mockWeatherEntities: HassEntity[] = [
    {
      entity_id: 'sensor.outdoor_temperature',
      name: 'Outdoor Temperature',
      state: '15',
      attributes: { friendly_name: 'Outdoor Temperature' },
    },
  ]

  const mockT = (key: string, defaultValue?: string) => defaultValue || key

  const mockOnUpdate = vi.fn()
  const mockOnLoadWeatherEntities = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns a SettingSection with correct id', () => {
    const section = SmartNightBoostSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
      weatherEntities: mockWeatherEntities,
      weatherEntitiesLoading: false,
      onLoadWeatherEntities: mockOnLoadWeatherEntities,
    })

    expect(section.id).toBe('smart-night-boost')
  })

  it('returns a SettingSection with correct title', () => {
    const section = SmartNightBoostSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
      weatherEntities: mockWeatherEntities,
      weatherEntitiesLoading: false,
      onLoadWeatherEntities: mockOnLoadWeatherEntities,
    })

    expect(section.title).toBe('settingsCards.smartNightBoostTitle')
  })

  it('shows LEARNING badge when smart boost is enabled', () => {
    const section = SmartNightBoostSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
      weatherEntities: mockWeatherEntities,
      weatherEntitiesLoading: false,
      onLoadWeatherEntities: mockOnLoadWeatherEntities,
    })

    expect(section.badge).toBe('LEARNING')
  })

  it('shows OFF badge when smart boost is disabled', () => {
    const disabledArea = { ...mockArea, smart_boost_enabled: false }
    const section = SmartNightBoostSection({
      area: disabledArea,
      onUpdate: mockOnUpdate,
      t: mockT,
      weatherEntities: mockWeatherEntities,
      weatherEntitiesLoading: false,
      onLoadWeatherEntities: mockOnLoadWeatherEntities,
    })

    expect(section.badge).toBe('OFF')
  })

  it('shows disabled message for airco heating type', () => {
    const aircoArea = { ...mockArea, heating_type: 'airco' as const }
    const section = SmartNightBoostSection({
      area: aircoArea,
      onUpdate: mockOnUpdate,
      t: mockT,
      weatherEntities: mockWeatherEntities,
      weatherEntitiesLoading: false,
      onLoadWeatherEntities: mockOnLoadWeatherEntities,
    })

    expect(section.description).toBe('Disabled for Air Conditioner')
  })

  it('has defaultExpanded set to false', () => {
    const section = SmartNightBoostSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
      weatherEntities: mockWeatherEntities,
      weatherEntitiesLoading: false,
      onLoadWeatherEntities: mockOnLoadWeatherEntities,
    })

    expect(section.defaultExpanded).toBe(false)
  })

  it('includes content', () => {
    const section = SmartNightBoostSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
      weatherEntities: mockWeatherEntities,
      weatherEntitiesLoading: false,
      onLoadWeatherEntities: mockOnLoadWeatherEntities,
    })

    expect(section.content).toBeDefined()
  })
})
