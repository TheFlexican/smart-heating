import { Box, FormControlLabel, Switch, Typography, Alert } from '@mui/material'
import SensorOccupiedIcon from '@mui/icons-material/SensorOccupied'
import { TFunction } from 'i18next'
import { Zone } from '../../types'
import { SettingSection } from '../DraggableSettings'
import { setAreaPresenceConfig } from '../../api/sensors'

export interface PresenceConfigSectionProps {
  area: Zone
  onUpdate: () => void
  t: TFunction
}

export const PresenceConfigSection = ({
  area,
  onUpdate,
  t,
}: PresenceConfigSectionProps): SettingSection => {
  return {
    id: 'presence-config',
    title: t('settingsCards.presenceConfigTitle'),
    description: t('settingsCards.presenceConfigDescription'),
    icon: <SensorOccupiedIcon />,
    defaultExpanded: false,
    content: (
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <FormControlLabel
          control={
            <Switch
              checked={area.use_global_presence ?? false}
              onChange={async e => {
                e.stopPropagation()
                const newValue = e.target.checked
                try {
                  await setAreaPresenceConfig(area.id, newValue)
                  // Force reload to get updated data
                  onUpdate()
                } catch (error) {
                  console.error('Failed to update presence config:', error)
                  alert(`Failed to update presence config: ${error}`)
                }
              }}
            />
          }
          label={
            <Box>
              <Typography variant="body1">
                {area.use_global_presence
                  ? t('settingsCards.useGlobalPresence')
                  : t('settingsCards.useAreaSpecificSensors')}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {area.use_global_presence
                  ? t('settingsCards.useGlobalPresenceDescription')
                  : t('settingsCards.useAreaSpecificDescription')}
              </Typography>
            </Box>
          }
        />

        <Alert severity="info">{t('settingsCards.presenceToggleInfo')}</Alert>
      </Box>
    ),
  }
}
