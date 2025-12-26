import { describe, it, expect, vi, beforeEach } from 'vitest'
import { Zone } from '../../types'
import { BoostModeSection } from './BoostModeSection'

// Mock the API functions
vi.mock('../../api/areas', () => ({
  setBoostMode: vi.fn(),
  cancelBoost: vi.fn(),
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

describe('BoostModeSection', () => {
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
    boost_mode_active: false,
  }

  const mockOnUpdate = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns a SettingSection with correct id', () => {
    const mockT = (key: string) => key
    const section = BoostModeSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.id).toBe('boost-mode')
  })

  it('returns a SettingSection with correct title', () => {
    const mockT = (key: string) => key
    const section = BoostModeSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.title).toBe('settingsCards.boostModeTitle')
  })

  it('shows ACTIVE badge when boost mode is active', () => {
    const mockT = (key: string) => key
    const activeArea = { ...mockArea, boost_mode_active: true }
    const section = BoostModeSection({
      area: activeArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.badge).toBe('ACTIVE')
  })

  it('does not show badge when boost mode is inactive', () => {
    const mockT = (key: string) => key
    const section = BoostModeSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.badge).toBeUndefined()
  })

  it('sets defaultExpanded to true when boost mode is active', () => {
    const mockT = (key: string) => key
    const activeArea = { ...mockArea, boost_mode_active: true }
    const section = BoostModeSection({
      area: activeArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.defaultExpanded).toBe(true)
  })

  it('sets defaultExpanded to false when boost mode is inactive', () => {
    const mockT = (key: string) => key
    const section = BoostModeSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.defaultExpanded).toBe(false)
  })

  it('shows disabled message for airco heating type', () => {
    const mockT = (key: string) => key
    const aircoArea = { ...mockArea, heating_type: 'airco' as const }
    const section = BoostModeSection({
      area: aircoArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.description).toContain('disabledForAirco')
  })

  it('includes content', () => {
    const mockT = (key: string) => key
    const section = BoostModeSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.content).toBeDefined()
  })
})
