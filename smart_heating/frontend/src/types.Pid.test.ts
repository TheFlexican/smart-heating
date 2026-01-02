import { describe, it, expect } from 'vitest'
import type { Zone, Area } from '../types'

describe('Types - PID Control Fields', () => {
  describe('Zone/Area Interface', () => {
    it('has pid_enabled field', () => {
      const area: Zone = {
        id: 'test',
        name: 'Test Area',
        enabled: true,
        state: 'idle',
        target_temperature: 20,
        devices: [],
        pid_enabled: true,
      }

      expect(area.pid_enabled).toBe(true)
      expect(typeof area.pid_enabled).toBe('boolean')
    })

    it('has pid_automatic_gains field', () => {
      const area: Zone = {
        id: 'test',
        name: 'Test Area',
        enabled: true,
        state: 'idle',
        target_temperature: 20,
        devices: [],
        pid_automatic_gains: false,
      }

      expect(area.pid_automatic_gains).toBe(false)
      expect(typeof area.pid_automatic_gains).toBe('boolean')
    })

    it('has pid_active_modes field', () => {
      const area: Zone = {
        id: 'test',
        name: 'Test Area',
        enabled: true,
        state: 'idle',
        target_temperature: 20,
        devices: [],
        pid_active_modes: ['schedule', 'home'],
      }

      expect(area.pid_active_modes).toEqual(['schedule', 'home'])
      expect(Array.isArray(area.pid_active_modes)).toBe(true)
    })

    it('allows all three PID fields together', () => {
      const area: Zone = {
        id: 'living_room',
        name: 'Living Room',
        enabled: true,
        state: 'heating',
        target_temperature: 21.5,
        devices: [],
        pid_enabled: true,
        pid_automatic_gains: true,
        pid_active_modes: ['schedule', 'home', 'comfort'],
      }

      expect(area.pid_enabled).toBe(true)
      expect(area.pid_automatic_gains).toBe(true)
      expect(area.pid_active_modes).toEqual(['schedule', 'home', 'comfort'])
    })

    it('makes PID fields optional', () => {
      // Should compile without PID fields
      const areaWithoutPid: Zone = {
        id: 'bedroom',
        name: 'Bedroom',
        enabled: true,
        state: 'idle',
        target_temperature: 19,
        devices: [],
      }

      expect(areaWithoutPid.pid_enabled).toBeUndefined()
      expect(areaWithoutPid.pid_automatic_gains).toBeUndefined()
      expect(areaWithoutPid.pid_active_modes).toBeUndefined()
    })

    it('accepts undefined for PID fields', () => {
      const area: Zone = {
        id: 'test',
        name: 'Test',
        enabled: true,
        state: 'off',
        target_temperature: 20,
        devices: [],
        pid_enabled: undefined,
        pid_automatic_gains: undefined,
        pid_active_modes: undefined,
      }

      expect(area.pid_enabled).toBeUndefined()
      expect(area.pid_automatic_gains).toBeUndefined()
      expect(area.pid_active_modes).toBeUndefined()
    })
  })

  describe('Area Type Alias', () => {
    it('Area is alias for Zone', () => {
      const zone: Zone = {
        id: 'test',
        name: 'Test',
        enabled: true,
        state: 'idle',
        target_temperature: 20,
        devices: [],
        pid_enabled: true,
      }

      // Should be assignable to Area type
      const area: Area = zone

      expect(area.pid_enabled).toBe(true)
    })

    it('Area has same PID fields as Zone', () => {
      const area: Area = {
        id: 'office',
        name: 'Office',
        enabled: true,
        state: 'heating',
        target_temperature: 22,
        devices: [],
        pid_enabled: false,
        pid_automatic_gains: true,
        pid_active_modes: ['home', 'comfort'],
      }

      expect(area.pid_enabled).toBe(false)
      expect(area.pid_automatic_gains).toBe(true)
      expect(area.pid_active_modes).toEqual(['home', 'comfort'])
    })
  })

  describe('PID Field Types', () => {
    it('pid_enabled accepts only boolean', () => {
      const area: Zone = {
        id: 'test',
        name: 'Test',
        enabled: true,
        state: 'idle',
        target_temperature: 20,
        devices: [],
        pid_enabled: true,
      }

      // TypeScript enforces boolean type
      expect(typeof area.pid_enabled).toBe('boolean')

      // These would fail TypeScript compilation:
      // pid_enabled: 'true'
      // pid_enabled: 1
      // pid_enabled: null
    })

    it('pid_automatic_gains accepts only boolean', () => {
      const area: Zone = {
        id: 'test',
        name: 'Test',
        enabled: true,
        state: 'idle',
        target_temperature: 20,
        devices: [],
        pid_automatic_gains: false,
      }

      expect(typeof area.pid_automatic_gains).toBe('boolean')

      // These would fail TypeScript compilation:
      // pid_automatic_gains: 'false'
      // pid_automatic_gains: 0
    })

    it('pid_active_modes accepts only string array', () => {
      const area: Zone = {
        id: 'test',
        name: 'Test',
        enabled: true,
        state: 'idle',
        target_temperature: 20,
        devices: [],
        pid_active_modes: ['schedule', 'home'],
      }

      expect(Array.isArray(area.pid_active_modes)).toBe(true)
      expect(area.pid_active_modes?.every(m => typeof m === 'string')).toBe(true)

      // These would fail TypeScript compilation:
      // pid_active_modes: 'schedule'
      // pid_active_modes: [1, 2, 3]
      // pid_active_modes: { schedule: true }
    })

    it('pid_active_modes accepts empty array', () => {
      const area: Zone = {
        id: 'test',
        name: 'Test',
        enabled: true,
        state: 'idle',
        target_temperature: 20,
        devices: [],
        pid_active_modes: [],
      }

      expect(area.pid_active_modes).toEqual([])
      expect(Array.isArray(area.pid_active_modes)).toBe(true)
      expect(area.pid_active_modes?.length).toBe(0)
    })
  })

  describe('Integration with Other Zone Fields', () => {
    it('PID fields coexist with heating_type', () => {
      const area: Zone = {
        id: 'test',
        name: 'Test',
        enabled: true,
        state: 'idle',
        target_temperature: 20,
        devices: [],
        heating_type: 'radiator',
        pid_enabled: true,
        pid_automatic_gains: true,
        pid_active_modes: ['schedule'],
      }

      expect(area.heating_type).toBe('radiator')
      expect(area.pid_enabled).toBe(true)
    })

    it('PID fields coexist with preset_mode', () => {
      const area: Zone = {
        id: 'test',
        name: 'Test',
        enabled: true,
        state: 'idle',
        target_temperature: 20,
        devices: [],
        preset_mode: 'home',
        pid_enabled: true,
        pid_active_modes: ['home', 'comfort'],
      }

      expect(area.preset_mode).toBe('home')
      expect(area.pid_active_modes).toContain('home')
    })

    it('PID fields coexist with boost mode', () => {
      const area: Zone = {
        id: 'test',
        name: 'Test',
        enabled: true,
        state: 'heating',
        target_temperature: 25,
        devices: [],
        boost_mode_active: true,
        boost_temp: 25,
        boost_duration: 30,
        pid_enabled: true,
        pid_active_modes: ['boost'],
      }

      expect(area.boost_mode_active).toBe(true)
      expect(area.pid_active_modes).toContain('boost')
    })

    it('PID fields coexist with schedules', () => {
      const area: Zone = {
        id: 'test',
        name: 'Test',
        enabled: true,
        state: 'idle',
        target_temperature: 20,
        devices: [],
        schedules: [
          {
            id: 'sched1',
            day: 0,
            start_time: '06:00',
            end_time: '22:00',
            temperature: 21,
          },
        ],
        pid_enabled: true,
        pid_active_modes: ['schedule'],
      }

      expect(area.schedules?.length).toBe(1)
      expect(area.pid_active_modes).toContain('schedule')
    })
  })

  describe('Real-World PID Configurations', () => {
    it('typical PID enabled configuration', () => {
      const area: Zone = {
        id: 'living_room',
        name: 'Living Room',
        enabled: true,
        state: 'heating',
        target_temperature: 21.5,
        current_temperature: 20.2,
        devices: [],
        heating_type: 'radiator',
        preset_mode: 'home',
        pid_enabled: true,
        pid_automatic_gains: true,
        pid_active_modes: ['schedule', 'home', 'comfort'],
      }

      expect(area.pid_enabled).toBe(true)
      expect(area.pid_automatic_gains).toBe(true)
      expect(area.pid_active_modes).toHaveLength(3)
    })

    it('PID disabled configuration', () => {
      const area: Zone = {
        id: 'bedroom',
        name: 'Bedroom',
        enabled: true,
        state: 'idle',
        target_temperature: 18,
        devices: [],
        heating_type: 'radiator',
        pid_enabled: false,
        pid_automatic_gains: true,
        pid_active_modes: ['schedule'],
      }

      expect(area.pid_enabled).toBe(false)
      // Other fields still present but not active
      expect(area.pid_automatic_gains).toBe(true)
      expect(area.pid_active_modes).toHaveLength(1)
    })

    it('manual PID gains configuration', () => {
      const area: Zone = {
        id: 'office',
        name: 'Office',
        enabled: true,
        state: 'heating',
        target_temperature: 22,
        devices: [],
        heating_type: 'radiator',
        pid_enabled: true,
        pid_automatic_gains: false,
        pid_active_modes: ['schedule', 'home'],
      }

      expect(area.pid_enabled).toBe(true)
      expect(area.pid_automatic_gains).toBe(false)
    })

    it('selective mode activation', () => {
      const area: Zone = {
        id: 'kitchen',
        name: 'Kitchen',
        enabled: true,
        state: 'idle',
        target_temperature: 19,
        devices: [],
        pid_enabled: true,
        pid_automatic_gains: true,
        pid_active_modes: ['home', 'comfort'], // Not active in schedule or away
      }

      expect(area.pid_active_modes).not.toContain('schedule')
      expect(area.pid_active_modes).not.toContain('away')
      expect(area.pid_active_modes).toContain('home')
      expect(area.pid_active_modes).toContain('comfort')
    })

    it('all modes active configuration', () => {
      const area: Zone = {
        id: 'test',
        name: 'Test',
        enabled: true,
        state: 'idle',
        target_temperature: 20,
        devices: [],
        pid_enabled: true,
        pid_automatic_gains: true,
        pid_active_modes: ['schedule', 'home', 'away', 'sleep', 'comfort', 'eco', 'boost'],
      }

      expect(area.pid_active_modes).toHaveLength(7)
      expect(area.pid_active_modes).toContain('schedule')
      expect(area.pid_active_modes).toContain('home')
      expect(area.pid_active_modes).toContain('away')
      expect(area.pid_active_modes).toContain('sleep')
      expect(area.pid_active_modes).toContain('comfort')
      expect(area.pid_active_modes).toContain('eco')
      expect(area.pid_active_modes).toContain('boost')
    })
  })
})
