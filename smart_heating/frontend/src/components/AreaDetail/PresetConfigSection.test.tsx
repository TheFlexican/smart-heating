import { describe, it, expect, vi, beforeEach } from 'vitest'
import { Zone, GlobalPresets } from '../../types'
import { PresetConfigSection } from './PresetConfigSection'

// Mock the API functions
vi.mock('../../api/areas', () => ({
  setAreaPresetConfig: vi.fn(),
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

describe('PresetConfigSection', () => {
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
    away_temp: 16,
    eco_temp: 18,
    comfort_temp: 22,
    home_temp: 21,
    sleep_temp: 19,
    activity_temp: 23,
    use_global_away: true,
    use_global_eco: true,
    use_global_comfort: false,
    use_global_home: true,
    use_global_sleep: true,
    use_global_activity: true,
  }

  const mockGlobalPresets: GlobalPresets = {
    away_temp: 16,
    eco_temp: 18,
    comfort_temp: 22,
    home_temp: 21,
    sleep_temp: 19,
    activity_temp: 23,
  }

  const mockOnUpdate = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns a SettingSection with correct id', () => {
    const mockT = (key: string) => key
    const section = PresetConfigSection({
      area: mockArea,
      globalPresets: mockGlobalPresets,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.id).toBe('preset-config')
  })

  it('returns a SettingSection with correct title', () => {
    const mockT = (key: string) => key
    const section = PresetConfigSection({
      area: mockArea,
      globalPresets: mockGlobalPresets,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.title).toBe('settingsCards.presetTemperatureConfigTitle')
  })

  it('has defaultExpanded set to false', () => {
    const mockT = (key: string) => key
    const section = PresetConfigSection({
      area: mockArea,
      globalPresets: mockGlobalPresets,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.defaultExpanded).toBe(false)
  })

  it('includes content with preset configuration', () => {
    const mockT = (key: string) => key
    const section = PresetConfigSection({
      area: mockArea,
      globalPresets: mockGlobalPresets,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.content).toBeDefined()
  })
})
