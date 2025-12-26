import { describe, it, expect, vi, beforeEach } from 'vitest'
import { Zone } from '../../types'
import { SwitchControlSection } from './SwitchControlSection'

// Mock the API functions
vi.mock('../../api/areas', () => ({
  setSwitchShutdown: vi.fn(),
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

describe('SwitchControlSection', () => {
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
    shutdown_switches_when_idle: true,
  }

  const mockOnUpdate = vi.fn()
  const mockT = (key: string) => key

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns a SettingSection with correct id', () => {
    const section = SwitchControlSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.id).toBe('switch-control')
  })

  it('returns a SettingSection with correct title', () => {
    const section = SwitchControlSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.title).toBe('settingsCards.switchPumpControlTitle')
  })

  it('shows "Auto Off" badge when shutdown_switches_when_idle is true', () => {
    const section = SwitchControlSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.badge).toBe('Auto Off')
  })

  it('shows "Always On" badge when shutdown_switches_when_idle is false', () => {
    const area = { ...mockArea, shutdown_switches_when_idle: false }
    const section = SwitchControlSection({
      area,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.badge).toBe('Always On')
  })

  it('defaults to "Auto Off" badge when shutdown_switches_when_idle is undefined', () => {
    const area = { ...mockArea, shutdown_switches_when_idle: undefined }
    const section = SwitchControlSection({
      area,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.badge).toBe('Auto Off')
  })

  it('sets defaultExpanded to false', () => {
    const section = SwitchControlSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.defaultExpanded).toBe(false)
  })

  it('includes content', () => {
    const section = SwitchControlSection({
      area: mockArea,
      onUpdate: mockOnUpdate,
      t: mockT,
    })

    expect(section.content).toBeDefined()
  })
})
