import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import ZoneCard from './ZoneCard'

const navigateMock = vi.fn()
vi.mock('react-router-dom', () => ({ useNavigate: () => navigateMock }))
vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string) => k }) }))

it('clicking card does not navigate and settings menu does not rely on card click', async () => {
  const onUpdate = vi.fn()
  const area: any = {
    id: 'a1',
    name: 'Test',
    enabled: true,
    state: 'idle',
    manual_override: false,
    target_temperature: 20,
    effective_target_temperature: 20,
    preset_mode: 'none',
    presence_sensors: [],
    devices: [],
    boost_mode_active: false,
    boost_temp: 0,
    boost_duration: 0,
    hidden: false,
  }

  render(<ZoneCard area={area} onUpdate={onUpdate} />)

  const card = screen.getByTestId('area-card-test')
  await userEvent.click(card)
  expect(navigateMock).not.toHaveBeenCalled()
})
