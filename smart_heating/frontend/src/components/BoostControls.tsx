import React, { useState } from 'react'
import { Box, TextField, Button, Alert } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Zone } from '../types'
import { setBoostMode, cancelBoost } from '../api/areas'

interface Props {
  area: Zone
  loadData: () => Promise<void>
}

const BoostControls: React.FC<Props> = ({ area, loadData }) => {
  const { t } = useTranslation()
  const [temp, setTemp] = useState<number>(25)
  const [duration, setDuration] = useState<number>(60)

  if (area.heating_type === 'airco') {
    return (
      <Alert severity="info" data-testid="boost-mode-disabled-airco">
        {t('settingsCards.disabledForAirco', 'Disabled for Air Conditioner')}
      </Alert>
    )
  }

  if (area.boost_mode_active) {
    return (
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
              await loadData()
            } catch (error) {
              console.error('Failed to cancel boost:', error)
            }
          }}
        >
          Cancel Boost Mode
        </Button>
      </Box>
    )
  }

  return (
    <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-end' }}>
      <TextField
        data-testid="boost-temperature-input"
        label="Boost Temperature"
        type="number"
        value={temp}
        onChange={e => setTemp(Number(e.target.value))}
        slotProps={{ htmlInput: { min: 15, max: 30, step: 0.5 } }}
        sx={{ flex: 1 }}
        id="boost-temp-input"
      />
      <TextField
        data-testid="boost-duration-input"
        label="Duration (minutes)"
        type="number"
        value={duration}
        onChange={e => setDuration(Number(e.target.value))}
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
            await setBoostMode(area.id, duration, temp)
            await loadData()
          } catch (error) {
            console.error('Failed to activate boost:', error)
          }
        }}
      >
        Activate Boost
      </Button>
    </Box>
  )
}

export default BoostControls
