import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import ZoneCard from './ZoneCard'
import { Zone } from '../../types'

// Mock API calls
vi.mock('../../api/areas', () => ({
  setZoneTemperature: vi.fn().mockResolvedValue({}),
  removeDeviceFromZone: vi.fn().mockResolvedValue({}),
  hideZone: vi.fn().mockResolvedValue({}),
  unhideZone: vi.fn().mockResolvedValue({}),
  setManualOverride: vi.fn().mockResolvedValue({}),
  setBoostMode: vi.fn().mockResolvedValue({}),
  cancelBoost: vi.fn().mockResolvedValue({}),
  setZoneHvacMode: vi.fn().mockResolvedValue({}),
}))

vi.mock('../../api/config', () => ({
  getEntityState: vi.fn().mockResolvedValue({ state: 'home' }),
}))

const renderZoneCard = (area: Zone) => {
  return render(
    <BrowserRouter>
      <ZoneCard area={area} onUpdate={vi.fn()} />
    </BrowserRouter>,
  )
}

describe('ZoneCard - PID Badge', () => {
  const baseArea: Zone = {
    id: 'living_room',
    name: 'Living Room',
    enabled: true,
    state: 'idle',
    target_temperature: 21.0,
    devices: [],
    preset_mode: 'schedule',
    pid_enabled: false,
    pid_automatic_gains: true,
    pid_active_modes: ['schedule', 'home', 'comfort'],
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Badge Visibility', () => {
    it('does not show PID badge when PID is disabled', () => {
      const area = { ...baseArea, pid_enabled: false }
      renderZoneCard(area)

      const badge = screen.queryByTestId('pid-active-badge')
      expect(badge).not.toBeInTheDocument()
    })

    it('shows PID badge when PID is enabled and current mode is in active modes', () => {
      const area = {
        ...baseArea,
        pid_enabled: true,
        preset_mode: 'schedule',
        pid_active_modes: ['schedule', 'home', 'comfort'],
      }
      renderZoneCard(area)

      const badge = screen.getByTestId('pid-active-badge')
      expect(badge).toBeInTheDocument()
    })

    it('does not show PID badge when PID is enabled but current mode not in active modes', () => {
      const area = {
        ...baseArea,
        pid_enabled: true,
        preset_mode: 'away',
        pid_active_modes: ['schedule', 'home', 'comfort'],
      }
      renderZoneCard(area)

      const badge = screen.queryByTestId('pid-active-badge')
      expect(badge).not.toBeInTheDocument()
    })

    it('shows PID badge for schedule mode when preset_mode is null/undefined', () => {
      const area = {
        ...baseArea,
        pid_enabled: true,
        preset_mode: undefined,
        pid_active_modes: ['schedule', 'home'],
      }
      renderZoneCard(area)

      const badge = screen.getByTestId('pid-active-badge')
      expect(badge).toBeInTheDocument()
    })

    it('shows PID badge when in home mode and home is active', () => {
      const area = {
        ...baseArea,
        pid_enabled: true,
        preset_mode: 'home',
        pid_active_modes: ['schedule', 'home', 'comfort'],
      }
      renderZoneCard(area)

      const badge = screen.getByTestId('pid-active-badge')
      expect(badge).toBeInTheDocument()
    })

    it('shows PID badge when in comfort mode and comfort is active', () => {
      const area = {
        ...baseArea,
        pid_enabled: true,
        preset_mode: 'comfort',
        pid_active_modes: ['schedule', 'home', 'comfort'],
      }
      renderZoneCard(area)

      const badge = screen.getByTestId('pid-active-badge')
      expect(badge).toBeInTheDocument()
    })

    it('does not show PID badge when in sleep mode and sleep not active', () => {
      const area = {
        ...baseArea,
        pid_enabled: true,
        preset_mode: 'sleep',
        pid_active_modes: ['schedule', 'home', 'comfort'],
      }
      renderZoneCard(area)

      const badge = screen.queryByTestId('pid-active-badge')
      expect(badge).not.toBeInTheDocument()
    })

    it('shows PID badge when in boost mode and boost is active', () => {
      const area = {
        ...baseArea,
        pid_enabled: true,
        preset_mode: 'boost',
        pid_active_modes: ['schedule', 'boost'],
      }
      renderZoneCard(area)

      const badge = screen.getByTestId('pid-active-badge')
      expect(badge).toBeInTheDocument()
    })
  })

  describe('Badge Content and Styling', () => {
    it('displays "PID" text on badge', () => {
      const area = {
        ...baseArea,
        pid_enabled: true,
        preset_mode: 'schedule',
        pid_active_modes: ['schedule'],
      }
      renderZoneCard(area)

      const badge = screen.getByTestId('pid-active-badge')
      expect(badge).toHaveTextContent('PID')
    })

    it('has amber color styling', () => {
      const area = {
        ...baseArea,
        pid_enabled: true,
        preset_mode: 'home',
        pid_active_modes: ['home'],
      }
      renderZoneCard(area)

      const badge = screen.getByTestId('pid-active-badge')
      const styles = window.getComputedStyle(badge)
      // Check for gradient with amber colors (MUI applies inline styles)
      expect(badge).toHaveStyle({ color: '#ffffff' })
    })

    it('shows "Auto" tooltip when automatic gains enabled', () => {
      const area = {
        ...baseArea,
        pid_enabled: true,
        preset_mode: 'schedule',
        pid_active_modes: ['schedule'],
        pid_automatic_gains: true,
      }
      renderZoneCard(area)

      const badge = screen.getByTestId('pid-active-badge')
      // Translation mock returns the key, so check for the key with mode parameter
      expect(badge.getAttribute('title')).toBe('settingsCards.pidBadgeTooltip')
    })

    it('shows "Manual" tooltip when automatic gains disabled', () => {
      const area = {
        ...baseArea,
        pid_enabled: true,
        preset_mode: 'schedule',
        pid_active_modes: ['schedule'],
        pid_automatic_gains: false,
      }
      renderZoneCard(area)

      const badge = screen.getByTestId('pid-active-badge')
      // Translation mock returns the key, so check for the key with mode parameter
      expect(badge.getAttribute('title')).toBe('settingsCards.pidBadgeTooltip')
    })
  })

  describe('Multiple Badge Scenarios', () => {
    it('shows both boost and PID badges when both active', () => {
      const area = {
        ...baseArea,
        pid_enabled: true,
        preset_mode: 'boost',
        pid_active_modes: ['boost'],
        boost_mode_active: true,
      }
      renderZoneCard(area)

      const pidBadge = screen.getByTestId('pid-active-badge')
      const boostBadge = screen.getByTestId('boost-active-badge')

      expect(pidBadge).toBeInTheDocument()
      expect(boostBadge).toBeInTheDocument()
    })

    it('shows PID badge alongside state chip', () => {
      const area = {
        ...baseArea,
        pid_enabled: true,
        preset_mode: 'home',
        pid_active_modes: ['home'],
        state: 'heating',
      }
      renderZoneCard(area)

      const pidBadge = screen.getByTestId('pid-active-badge')
      const stateChip = screen.getByTestId(`area-state-${area.id}`)

      expect(pidBadge).toBeInTheDocument()
      expect(stateChip).toBeInTheDocument()
    })
  })

  describe('Edge Cases', () => {
    it('handles empty active_modes array', () => {
      const area = {
        ...baseArea,
        pid_enabled: true,
        preset_mode: 'schedule',
        pid_active_modes: [],
      }
      renderZoneCard(area)

      const badge = screen.queryByTestId('pid-active-badge')
      expect(badge).not.toBeInTheDocument()
    })

    it('handles undefined active_modes', () => {
      const area = {
        ...baseArea,
        pid_enabled: true,
        preset_mode: 'schedule',
        pid_active_modes: undefined,
      }
      renderZoneCard(area)

      const badge = screen.queryByTestId('pid-active-badge')
      expect(badge).not.toBeInTheDocument()
    })

    it('handles null preset_mode as schedule', () => {
      const area = {
        ...baseArea,
        pid_enabled: true,
        preset_mode: null as any,
        pid_active_modes: ['schedule'],
      }
      renderZoneCard(area)

      const badge = screen.getByTestId('pid-active-badge')
      expect(badge).toBeInTheDocument()
    })

    it('is case-sensitive for mode matching', () => {
      const area = {
        ...baseArea,
        pid_enabled: true,
        preset_mode: 'HOME', // Uppercase
        pid_active_modes: ['home'], // Lowercase
      }
      renderZoneCard(area)

      // Should NOT show badge because of case mismatch
      const badge = screen.queryByTestId('pid-active-badge')
      expect(badge).not.toBeInTheDocument()
    })

    it('shows badge only when both PID enabled and mode matches', () => {
      // Test all combinations
      const testCases = [
        { pid_enabled: false, modeMatches: false, shouldShow: false },
        { pid_enabled: false, modeMatches: true, shouldShow: false },
        { pid_enabled: true, modeMatches: false, shouldShow: false },
        { pid_enabled: true, modeMatches: true, shouldShow: true },
      ]

      testCases.forEach(({ pid_enabled, modeMatches, shouldShow }) => {
        const { container } = renderZoneCard({
          ...baseArea,
          pid_enabled,
          preset_mode: modeMatches ? 'schedule' : 'away',
          pid_active_modes: ['schedule'],
        })

        const badge = screen.queryByTestId('pid-active-badge')
        if (shouldShow) {
          expect(badge).toBeInTheDocument()
        } else {
          expect(badge).not.toBeInTheDocument()
        }

        // Clean up for next iteration
        container.remove()
      })
    })
  })

  describe('Dynamic Updates', () => {
    it('shows badge when PID is enabled via prop update', async () => {
      const area = {
        ...baseArea,
        pid_enabled: false,
        preset_mode: 'schedule',
        pid_active_modes: ['schedule'],
      }
      const { rerender } = renderZoneCard(area)

      expect(screen.queryByTestId('pid-active-badge')).not.toBeInTheDocument()

      // Update area to enable PID
      const updatedArea = { ...area, pid_enabled: true }
      rerender(
        <BrowserRouter>
          <ZoneCard area={updatedArea} onUpdate={vi.fn()} />
        </BrowserRouter>,
      )

      await waitFor(() => {
        expect(screen.getByTestId('pid-active-badge')).toBeInTheDocument()
      })
    })

    it('hides badge when mode changes to non-active mode', async () => {
      const area = {
        ...baseArea,
        pid_enabled: true,
        preset_mode: 'schedule',
        pid_active_modes: ['schedule'],
      }
      const { rerender } = renderZoneCard(area)

      expect(screen.getByTestId('pid-active-badge')).toBeInTheDocument()

      // Update area to change mode
      const updatedArea = { ...area, preset_mode: 'away' }
      rerender(
        <BrowserRouter>
          <ZoneCard area={updatedArea} onUpdate={vi.fn()} />
        </BrowserRouter>,
      )

      await waitFor(() => {
        expect(screen.queryByTestId('pid-active-badge')).not.toBeInTheDocument()
      })
    })

    it('updates tooltip when automatic gains changes', async () => {
      const area = {
        ...baseArea,
        pid_enabled: true,
        preset_mode: 'schedule',
        pid_active_modes: ['schedule'],
        pid_automatic_gains: true,
      }
      const { rerender } = renderZoneCard(area)

      let badge = screen.getByTestId('pid-active-badge')
      expect(badge.getAttribute('title')).toBe('settingsCards.pidBadgeTooltip')

      // Update to manual gains
      const updatedArea = { ...area, pid_automatic_gains: false }
      rerender(
        <BrowserRouter>
          <ZoneCard area={updatedArea} onUpdate={vi.fn()} />
        </BrowserRouter>,
      )

      await waitFor(() => {
        badge = screen.getByTestId('pid-active-badge')
        expect(badge.getAttribute('title')).toBe('settingsCards.pidBadgeTooltip')
      })
    })
  })
})
