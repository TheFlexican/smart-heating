import { Box, FormControlLabel, Switch, Typography } from '@mui/material'
import PowerSettingsNewIcon from '@mui/icons-material/PowerSettingsNew'
import { TFunction } from 'i18next'
import { Zone } from '../../types'
import { SettingSection } from '../DraggableSettings'
import { setSwitchShutdown } from '../../api/areas'

export interface SwitchControlSectionProps {
  area: Zone
  onUpdate: () => void
  t: TFunction
}

export const SwitchControlSection = ({
  area,
  onUpdate,
  t,
}: SwitchControlSectionProps): SettingSection => {
  return {
    id: 'switch-control',
    title: t('settingsCards.switchPumpControlTitle'),
    description: t('settingsCards.switchPumpControlDescription'),
    icon: <PowerSettingsNewIcon />,
    badge: (area.shutdown_switches_when_idle ?? true) ? 'Auto Off' : 'Always On',
    defaultExpanded: false,
    content: (
      <Box>
        <FormControlLabel
          control={
            <Switch
              data-testid="shutdown-switches-input"
              checked={area.shutdown_switches_when_idle ?? true}
              disabled={area.heating_type === 'airco'}
              onChange={async e => {
                try {
                  await setSwitchShutdown(area.id, e.target.checked)
                  onUpdate()
                } catch (error) {
                  console.error('Failed to update switch shutdown setting:', error)
                }
              }}
            />
          }
          label={t('settingsCards.shutdownSwitchesPumps')}
        />
        <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1, ml: 4 }}>
          {area.heating_type === 'airco'
            ? t('settingsCards.disabledForAirco')
            : t('settingsCards.shutdownSwitchesDescription')}
        </Typography>
      </Box>
    ),
  }
}
