import { describe, it, expect, vi, beforeEach } from 'vitest'
import { Zone, GlobalPresets } from '../../types'
import { PresetModesSection } from './PresetModesSection'

// Mock the API functions
vi.mock('../../api/areas', () => ({
  setPresetMode: vi.fn(),
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

describe('PresetModesSection', () => {
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
    const section = PresetModesSection({
      area: mockArea,
      globalPresets: mockGlobalPresets,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.id).toBe('preset-modes')
  })

  it('returns a SettingSection with correct title', () => {
    const mockT = (key: string) => key
    const section = PresetModesSection({
      area: mockArea,
      globalPresets: mockGlobalPresets,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.title).toBe('settingsCards.presetModesTitle')
  })

  it('shows badge when area is enabled and preset mode is not none', () => {
    const mockT = (key: string) => key
    const section = PresetModesSection({
      area: mockArea,
      globalPresets: mockGlobalPresets,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.badge).toBe('presets.comfort')
  })

  it('does not show badge when area is disabled', () => {
    const disabledArea = { ...mockArea, enabled: false }
    const mockT = (key: string) => key
    const section = PresetModesSection({
      area: disabledArea,
      globalPresets: mockGlobalPresets,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.badge).toBeUndefined()
  })

  it('does not show badge when preset mode is none', () => {
    const noneArea = { ...mockArea, preset_mode: 'none' }
    const mockT = (key: string) => key
    const section = PresetModesSection({
      area: noneArea,
      globalPresets: mockGlobalPresets,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.badge).toBeUndefined()
  })

  it('has defaultExpanded set to false', () => {
    const mockT = (key: string) => key
    const section = PresetModesSection({
      area: mockArea,
      globalPresets: mockGlobalPresets,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.defaultExpanded).toBe(false)
  })

  it('includes content with FormControl', () => {
    const mockT = (key: string) => key
    const section = PresetModesSection({
      area: mockArea,
      globalPresets: mockGlobalPresets,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.content).toBeDefined()
  })
})
