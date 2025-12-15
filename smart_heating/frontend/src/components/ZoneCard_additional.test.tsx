import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import ZoneCard from './ZoneCard'
import { MemoryRouter } from 'react-router-dom'
import * as api from '../api/areas'

vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string) => k }) }))
vi.mock('../api/areas')

const mockedApi = api as unknown as Record<string, any>

describe('ZoneCard additional tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('displays thermostat and target arrow when target exceeds current', () => {
    const area = {
      id: 'a1',
      name: 'Living',
      enabled: true,
      state: 'heating',
      manual_override: false,
      target_temperature: 22,
      effective_target_temperature: 23,
      current_temperature: 20,
      devices: [
        {
          id: 'd1',
          type: 'thermostat',
          name: 'T1',
          current_temperature: 20,
          hvac_action: 'heating',
        },
      ],
      presence_sensors: [],
      boost_mode_active: false,
      devices_count: 1,
    }

    render(
      <MemoryRouter>
        <ZoneCard area={area as any} onUpdate={() => {}} />
      </MemoryRouter>
    )
    const temps = screen.getAllByText(/20.0°C/)
    expect(temps.length).toBeGreaterThan(0)
    expect(screen.getByText(/→ 22.0°C/)).toBeInTheDocument()
  })

  it('shows valve position and generic device state', () => {
    const area = {
      id: 'a2',
      name: 'Room',
      enabled: true,
      state: 'idle',
      manual_override: false,
      target_temperature: 20,
      devices: [
        { id: 'v1', type: 'valve', name: 'V1', position: 70 },
        { id: 'g1', type: 'switch', name: 'S1', state: 'on' },
      ],
      presence_sensors: [],
      boost_mode_active: false,
    }
    render(
      <MemoryRouter>
        <ZoneCard area={area as any} onUpdate={() => {}} />
      </MemoryRouter>
    )
    expect(screen.getByText(/70%/)).toBeInTheDocument()
    expect(screen.getByText('area.on')).toBeInTheDocument()
  })

  it('toggle hidden via menu calls hideZone/unhideZone', async () => {
    mockedApi.hideZone = vi.fn().mockResolvedValue({})
    mockedApi.unhideZone = vi.fn().mockResolvedValue({})
    const user = userEvent.setup()
    const area = {
      id: 'a3',
      name: 'H',
      enabled: true,
      state: 'idle',
      manual_override: false,
      hidden: false,
      devices: [],
      presence_sensors: [],
      boost_mode_active: false,
    } as any
    const { container } = render(
      <MemoryRouter>
        <ZoneCard area={area} onUpdate={() => {}} />
      </MemoryRouter>
    )
    const menuButton = Array.from(container.querySelectorAll('button')).find(b =>
      b.innerHTML.includes('MoreVertIcon')
    )
    await user.click(menuButton)
    const menuItem = screen.getByText('area.hideArea')
    await user.click(menuItem)
    expect(mockedApi.hideZone).toHaveBeenCalledWith('a3')
  })

  it('slider commit calls setZoneTemperature when manual', async () => {
    mockedApi.setZoneTemperature = vi.fn().mockResolvedValue({})
    const area = {
      id: 'a4',
      name: 'S',
      enabled: true,
      state: 'heating',
      manual_override: true,
      target_temperature: 21,
      devices: [{ id: 'd1' }],
      presence_sensors: [],
      boost_mode_active: false,
    } as any
    render(
      <MemoryRouter>
        <ZoneCard area={area} onUpdate={() => {}} />
      </MemoryRouter>
    )
    const slider = screen.getByRole('slider')
    fireEvent.change(slider, { target: { value: 22 } })
    fireEvent.mouseUp(slider)
    expect(mockedApi.setZoneTemperature).toHaveBeenCalled()
  })
})
