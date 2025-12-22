import React from 'react'
import { render, screen } from '@testing-library/react'
import { vi, describe, it, expect } from 'vitest'

vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string) => k }) }))
vi.mock('../../api/areas', () => ({
  setAreaPresetConfig: vi.fn(),
  setHvacMode: vi.fn(),
  setSwitchShutdown: vi.fn(),
  setAreaHeatingCurve: vi.fn(),
}))
vi.mock('../../api/sensors', () => ({ setAreaPresenceConfig: vi.fn() }))
vi.mock('../../api/history', () => ({ migrateHistoryStorage: vi.fn() }))

import AreaSettings from './AreaSettings'

const area = {
  id: 'area1',
  enabled: true,
  heating_type: 'radiator',
  boost_mode_active: false,
} as any

const globalPresets = {
  away_temp: 16,
  eco_temp: 18,
  comfort_temp: 21,
  home_temp: 20,
  sleep_temp: 17,
  activity_temp: 19,
} as any

describe('AreaSettings', () => {
  it('renders settings sections', () => {
    render(
      <AreaSettings
        area={area}
        globalPresets={globalPresets}
        entityStates={{}}
        loadData={async () => {}}
        storageBackend="json"
        databaseStats={{}}
        migrating={false}
        setMigrating={() => {}}
        historyRetention={30}
        recordInterval={60}
        loadHistoryConfig={async () => {}}
      />,
    )

    expect(screen.getByText('settingsCards.presetModesTitle')).toBeInTheDocument()
    expect(screen.getByText('settingsCards.presetTemperatureConfigTitle')).toBeInTheDocument()
  })
})
