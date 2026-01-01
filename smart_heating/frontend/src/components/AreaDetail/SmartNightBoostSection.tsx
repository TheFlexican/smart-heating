import {
  Box,
  Switch,
  Typography,
  Alert,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
} from '@mui/material'
import PsychologyIcon from '@mui/icons-material/Psychology'
import { TFunction } from 'i18next'
import { Zone, HassEntity } from '../../types'
import { SettingSection } from '../DraggableSettings'
import { setNightBoostConfig } from '../../api/areas'

const updateSmartBoost = async (
  areaId: string,
  data: Record<string, any>,
  onUpdate: () => void,
) => {
  try {
    await setNightBoostConfig(areaId, data)
    await new Promise(resolve => setTimeout(resolve, 500))
    onUpdate()
  } catch (error) {
    console.error('Failed to update smart night boost:', error)
    throw error
  }
}

export const SmartNightBoostSection = ({
  area,
  onUpdate,
  t,
  weatherEntities,
  weatherEntitiesLoading,
  onLoadWeatherEntities,
}: {
  area: Zone
  onUpdate: () => void
  t: TFunction
  weatherEntities: HassEntity[]
  weatherEntitiesLoading: boolean
  onLoadWeatherEntities: () => void
}): SettingSection => ({
  id: 'smart-night-boost',
  title: t('settingsCards.smartNightBoostTitle'),
  description:
    area.heating_type === 'airco'
      ? t('settingsCards.disabledForAirco', 'Disabled for Air Conditioner')
      : t('settingsCards.smartNightBoostDescription'),
  icon: <PsychologyIcon />,
  badge: area.smart_boost_enabled ? 'LEARNING' : 'OFF',
  defaultExpanded: false,
  content:
    area.heating_type === 'airco' ? (
      <Alert severity="info" data-testid="smart-night-boost-disabled-airco">
        {t('settingsCards.disabledForAirco', 'Disabled for Air Conditioner')}
      </Alert>
    ) : (
      <>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {t('settingsCards.smartNightBoostIntro')}
        </Typography>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box>
            <Typography variant="body1" color="text.primary">
              {t('settingsCards.enableSmartNightBoost')}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {t('settingsCards.enableSmartNightBoostDescription')}
            </Typography>
          </Box>
          <Switch
            checked={area.smart_boost_enabled ?? false}
            onChange={e =>
              updateSmartBoost(area.id, { smart_boost_enabled: e.target.checked }, onUpdate)
            }
          />
        </Box>
        <TextField
          label={t('settingsCards.targetWakeupTime')}
          type="time"
          value={area.smart_boost_target_time ?? '06:00'}
          data-testid="smart-night-boost-target-time-input"
          onChange={e =>
            updateSmartBoost(area.id, { smart_boost_target_time: e.target.value }, onUpdate)
          }
          disabled={!area.smart_boost_enabled}
          fullWidth
          helperText={t('settingsCards.targetWakeupTimeHelper')}
          slotProps={{ inputLabel: { shrink: true }, htmlInput: { step: 300 } }}
          sx={{ mb: 3 }}
        />
        <FormControl fullWidth sx={{ mb: 3 }} disabled={!area.smart_boost_enabled}>
          <InputLabel>{t('settingsCards.outdoorTemperatureSensor')}</InputLabel>
          <Select
            value={area.weather_entity_id || ''}
            onChange={e =>
              updateSmartBoost(area.id, { weather_entity_id: e.target.value || null }, onUpdate)
            }
            onOpen={() => {
              if (weatherEntities.length === 0) onLoadWeatherEntities()
            }}
            label={t('settingsCards.outdoorTemperatureSensor')}
          >
            <MenuItem value="">
              <em>{t('settingsCards.outdoorTemperatureSensorPlaceholder')}</em>
            </MenuItem>
            {weatherEntitiesLoading ? (
              <MenuItem disabled>
                <CircularProgress size={20} sx={{ mr: 1 }} />
                Loading...
              </MenuItem>
            ) : (
              weatherEntities.map(entity => (
                <MenuItem key={entity.entity_id} value={entity.entity_id}>
                  {entity.attributes?.friendly_name || entity.entity_id}
                </MenuItem>
              ))
            )}
          </Select>
          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
            {t('settingsCards.outdoorTemperatureSensorHelper')}
          </Typography>
        </FormControl>
        {area.smart_boost_enabled && (
          <Box sx={{ mt: 3, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              <strong>{t('settingsCards.smartNightBoostHowItWorksTitle')}</strong>
            </Typography>
            <Typography variant="caption" color="text.secondary" component="div">
              • {t('settingsCards.smartNightBoostBullet1')}
              <br />• {t('settingsCards.smartNightBoostBullet2')}
              <br />• {t('settingsCards.smartNightBoostBullet3')}
              <br />• {t('settingsCards.smartNightBoostBullet4')}
            </Typography>
          </Box>
        )}
      </>
    ),
})
