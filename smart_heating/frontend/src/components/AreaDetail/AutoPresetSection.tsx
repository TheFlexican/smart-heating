import {
  Box,
  Switch,
  Typography,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material'
import PersonIcon from '@mui/icons-material/Person'
import { TFunction } from 'i18next'
import { Zone } from '../../types'
import { SettingSection } from '../DraggableSettings'
import { setAutoPreset } from '../../api/areas'

export const AutoPresetSection = ({
  area,
  onUpdate,
  t,
}: {
  area: Zone
  onUpdate: () => void
  t: TFunction
}): SettingSection => ({
  id: 'auto-preset',
  title: t('settingsCards.autoPresetTitle'),
  description: t('settingsCards.autoPresetDescription'),
  icon: <PersonIcon />,
  badge: area.auto_preset_enabled ? 'AUTO' : 'OFF',
  defaultExpanded: false,
  content: (
    <>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="body1" color="text.primary">
            {t('settingsCards.enableAutoPreset')}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {t('settingsCards.enableAutoPresetDescription')}
          </Typography>
        </Box>
        <Switch
          data-testid="auto-preset-toggle"
          checked={area.auto_preset_enabled ?? false}
          onChange={async e => {
            try {
              await setAutoPreset(area.id, {
                auto_preset_enabled: e.target.checked,
              })
              onUpdate()
            } catch (error) {
              console.error('Failed to update auto preset:', error)
            }
          }}
        />
      </Box>
      {area.auto_preset_enabled && (
        <>
          <Alert severity="info" sx={{ mb: 3 }}>
            {t('settingsCards.autoPresetExplanation')}
          </Alert>
          <Box sx={{ mb: 3 }}>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>{t('settingsCards.presetWhenHome')}</InputLabel>
              <Select
                value={area.auto_preset_home || 'home'}
                label={t('settingsCards.presetWhenHome')}
                onChange={async e => {
                  try {
                    await setAutoPreset(area.id, {
                      auto_preset_home: e.target.value as string,
                    })
                    onUpdate()
                  } catch (error) {
                    console.error('Failed to update home preset:', error)
                  }
                }}
              >
                <MenuItem value="home">{t('settingsCards.presetHome')}</MenuItem>
                <MenuItem value="comfort">{t('settingsCards.presetComfort')}</MenuItem>
                <MenuItem value="activity">{t('settingsCards.presetActivity')}</MenuItem>
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel>{t('settingsCards.presetWhenAway')}</InputLabel>
              <Select
                value={area.auto_preset_away || 'away'}
                label={t('settingsCards.presetWhenAway')}
                onChange={async e => {
                  try {
                    await setAutoPreset(area.id, {
                      auto_preset_away: e.target.value as string,
                    })
                    onUpdate()
                  } catch (error) {
                    console.error('Failed to update away preset:', error)
                  }
                }}
              >
                <MenuItem value="away">{t('settingsCards.presetAway')}</MenuItem>
                <MenuItem value="eco">{t('settingsCards.presetEco')}</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </>
      )}
      {!area.auto_preset_enabled && (
        <Alert severity="warning">{t('settingsCards.autoPresetDisabled')}</Alert>
      )}
    </>
  ),
})
