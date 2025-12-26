import { describe, it, expect, vi, beforeEach } from 'vitest'
import { Zone } from '../../types'
import { HvacModeSection } from './HvacModeSection'

// Mock the API functions
vi.mock('../../api/areas', () => ({
  setHvacMode: vi.fn(),
}))

describe('HvacModeSection', () => {
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
    hvac_mode: 'heat',
  }

  const mockOnUpdate = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns a SettingSection with correct id', () => {
    const section = HvacModeSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
    })

    expect(section.id).toBe('hvac-mode')
  })

  it('returns a SettingSection with correct title', () => {
    const section = HvacModeSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
    })

    expect(section.title).toBe('HVAC Mode')
  })

  it('returns a SettingSection with correct description', () => {
    const section = HvacModeSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
    })

    expect(section.description).toBe('Control the heating/cooling mode for this area')
  })

  it('shows current hvac_mode as badge', () => {
    const section = HvacModeSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
    })

    expect(section.badge).toBe('heat')
  })

  it('defaults badge to heat when hvac_mode is not set', () => {
    const areaWithoutMode = { ...mockArea, hvac_mode: undefined }
    const section = HvacModeSection({
      area: areaWithoutMode,
      onUpdate: mockOnUpdate,
    })

    expect(section.badge).toBe('heat')
  })

  it('has defaultExpanded set to false', () => {
    const section = HvacModeSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
    })

    expect(section.defaultExpanded).toBe(false)
  })

  it('includes content with FormControl', () => {
    const section = HvacModeSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
    })

    expect(section.content).toBeDefined()
  })
})
