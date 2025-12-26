import { describe, it, expect, vi, beforeEach } from 'vitest'
import { Zone } from '../../types'
import { HeatingTypeSection } from './HeatingTypeSection'

// Mock the API functions
vi.mock('../../api/areas', () => ({
  setHeatingType: vi.fn(),
  setAreaHeatingCurve: vi.fn(),
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

describe('HeatingTypeSection', () => {
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
    heating_type: 'radiator',
  }

  const mockOnUpdate = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns a SettingSection with correct id', () => {
    const mockT = (key: string) => key
    const section = HeatingTypeSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.id).toBe('heating-type')
  })

  it('returns a SettingSection with correct title', () => {
    const mockT = (key: string) => key
    const section = HeatingTypeSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.title).toContain('heatingTypeTitle')
  })

  it('shows Radiator badge for radiator heating type', () => {
    const mockT = (key: string) => key
    const section = HeatingTypeSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.badge).toContain('radiator')
  })

  it('shows Floor Heating badge for floor_heating type', () => {
    const floorArea = { ...mockArea, heating_type: 'floor_heating' as const }
    const mockT = (key: string) => key
    const section = HeatingTypeSection({
      area: floorArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.badge).toContain('floorHeating')
  })

  it('shows Air Conditioner badge for airco type', () => {
    const aircoArea = { ...mockArea, heating_type: 'airco' as const }
    const mockT = (key: string) => key
    const section = HeatingTypeSection({
      area: aircoArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.badge).toContain('airConditioner')
  })

  it('has defaultExpanded set to false', () => {
    const mockT = (key: string) => key
    const section = HeatingTypeSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.defaultExpanded).toBe(false)
  })

  it('includes content with RadioGroup', () => {
    const mockT = (key: string) => key
    const section = HeatingTypeSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.content).toBeDefined()
  })
})
