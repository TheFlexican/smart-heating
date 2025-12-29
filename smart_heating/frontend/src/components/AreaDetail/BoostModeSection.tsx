import { Box, Button, TextField, Alert } from '@mui/material'
import SpeedIcon from '@mui/icons-material/Speed'
import { TFunction } from 'i18next'
import { Zone } from '../../types'
import { SettingSection } from '../DraggableSettings'
import { setBoostMode, cancelBoost } from '../../api/areas'

export interface BoostModeSectionProps {
  area: Zone
  onUpdate: () => void
  t: TFunction
}

// Helper: Render disabled state for airco
const renderAircoDisabled = (t: TFunction) => (
  <Alert severity="info" data-testid="boost-mode-disabled-airco">
    {t('settingsCards.disabledForAirco', 'Disabled for Air Conditioner')}
  </Alert>
)

// Helper: Render active boost mode
const renderBoostActive = (area: Zone, onUpdate: () => void) => (
  <Box data-testid="boost-mode-active">
    <Alert severity="warning" sx={{ mb: 2 }}>
      Boost mode is <strong>ACTIVE</strong>! Temperature: {area.boost_temp}°C, Duration:{' '}
      {area.boost_duration} minutes
    </Alert>
    <Button
      variant="outlined"
      color="error"
      data-testid="cancel-boost-button"
      onClick={async () => {
        try {
          await cancelBoost(area.id)
          onUpdate()
        } catch (error) {
          console.error('Failed to cancel boost:', error)
        }
      }}
    >
      Cancel Boost Mode
    </Button>
  </Box>
)

// Helper: Render boost mode configuration form
const renderBoostForm = (area: Zone, onUpdate: () => void) => (
  <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-end' }}>
    <TextField
      data-testid="boost-temperature-input"
      label="Boost Temperature"
      type="number"
      defaultValue={25}
      slotProps={{ htmlInput: { min: 15, max: 30, step: 0.5 } }}
      sx={{ flex: 1 }}
      id="boost-temp-input"
    />
    <TextField
      data-testid="boost-duration-input"
      label="Duration (minutes)"
      type="number"
      defaultValue={60}
      slotProps={{ htmlInput: { min: 5, max: 180, step: 5 } }}
      sx={{ flex: 1 }}
      id="boost-duration-input"
    />
    <Button
      variant="contained"
      color="primary"
      data-testid="activate-boost-button"
      onClick={async () => {
        try {
          const tempInput = document.getElementById('boost-temp-input') as HTMLInputElement
          const durationInput = document.getElementById('boost-duration-input') as HTMLInputElement
          const temp = Number.parseFloat(tempInput.value)
          const duration = Number.parseInt(durationInput.value)
          await setBoostMode(area.id, duration, temp)
          onUpdate()
        } catch (error) {
          console.error('Failed to activate boost:', error)
        }
      }}
    >
      Activate Boost
    </Button>
  </Box>
)

// Helper: Get boost mode content based on area state
const getBoostContent = (area: Zone, onUpdate: () => void, t: TFunction) => {
  if (area.heating_type === 'airco') {
    return renderAircoDisabled(t)
  }
  if (area.boost_mode_active) {
    return renderBoostActive(area, onUpdate)
  }
  return renderBoostForm(area, onUpdate)
}

export const BoostModeSection = ({ area, onUpdate, t }: BoostModeSectionProps): SettingSection => {
  return {
    id: 'boost-mode',
    title: t('settingsCards.boostModeTitle'),
    description:
      area.heating_type === 'airco'
        ? t('settingsCards.disabledForAirco', 'Disabled for Air Conditioner')
        : t('settingsCards.boostModeDescription'),
    icon: <SpeedIcon />,
    badge: area.boost_mode_active ? 'ACTIVE' : undefined,
    defaultExpanded: area.boost_mode_active,
    content: getBoostContent(area, onUpdate, t),
  }
}
