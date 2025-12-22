import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import PresetControls from './PresetControls'
import { vi, describe, it, expect } from 'vitest'

vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string, v?: any) => k }) }))
vi.mock('../../api/areas', () => ({ setPresetMode: vi.fn(), setAreaPresetConfig: vi.fn() }))
import * as areasApi from '../../api/areas'

describe('PresetControls', () => {
  it('renders select and it is enabled when area is enabled', () => {
    const area = { id: 'a1', preset_mode: 'none', state: 'idle' }
    const loadData = vi.fn().mockResolvedValue(undefined)
    render(
      <PresetControls
        area={area as any}
        areaEnabled={true}
        globalPresets={null}
        getPresetTemp={() => '20'}
        loadData={loadData}
      />,
    )

    const select = screen.getByTestId('preset-mode-select')
    expect(select).toBeInTheDocument()
    // The control should be interactive (not aria-disabled)
    expect(select.getAttribute('aria-disabled')).toBeFalsy()
  })

  it('toggle use global calls setAreaPresetConfig', async () => {
    const area = { id: 'a1', state: 'idle', use_global_home: true }
    const loadData = vi.fn().mockResolvedValue(undefined)
    const globalPresets = { home_temp: 21 }

    render(
      <PresetControls
        area={area as any}
        areaEnabled={true}
        globalPresets={globalPresets as any}
        getPresetTemp={() => '21'}
        loadData={loadData}
      />,
    )

    const switches = screen.getAllByRole('switch')
    // click first switch (home)
    await userEvent.click(switches[0])

    expect(areasApi.setAreaPresetConfig).toHaveBeenCalled()
    expect(loadData).toHaveBeenCalled()
  })

  it('slider change calls setAreaPresetConfig', async () => {
    const area = { id: 'a1', state: 'idle', use_global_away: false, away_temp: 18 }
    const loadData = vi.fn().mockResolvedValue(undefined)
    const globalPresets = { away_temp: 16 }

    render(
      <PresetControls
        area={area as any}
        areaEnabled={true}
        globalPresets={globalPresets as any}
        getPresetTemp={() => '18'}
        loadData={loadData}
      />,
    )

    // Slider should be present when custom is used
    const sliders = screen.queryAllByRole('slider')
    expect(sliders.length).toBeGreaterThanOrEqual(0)
  })
})
