import { Box, Switch, Typography, Alert, TextField, Slider } from '@mui/material'
import NightsStayIcon from '@mui/icons-material/NightsStay'
import { TFunction } from 'i18next'
import { Zone } from '../../types'
import { SettingSection } from '../DraggableSettings'

const updateNightBoost = async (
  areaId: string,
  data: Record<string, any>,
  onUpdate: () => void,
) => {
  try {
    await fetch('/api/smart_heating/call_service', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ service: 'set_night_boost', area_id: areaId, ...data }),
    })
    onUpdate()
  } catch (error) {
    console.error('Failed to update night boost:', error)
  }
}

export const NightBoostSection = ({
  area,
  onUpdate,
  t,
}: {
  area: Zone
  onUpdate: () => void
  t: TFunction
}): SettingSection => ({
  id: 'night-boost',
  title: t('settingsCards.nightBoostTitle'),
  description:
    area.heating_type === 'airco'
      ? t('settingsCards.disabledForAirco', 'Disabled for Air Conditioner')
      : t('settingsCards.nightBoostDescription'),
  icon: <NightsStayIcon />,
  badge: area.night_boost_enabled ? 'ON' : 'OFF',
  defaultExpanded: false,
  content:
    area.heating_type === 'airco' ? (
      <Alert severity="info" data-testid="night-boost-disabled-airco">
        {t('settingsCards.disabledForAirco', 'Disabled for Air Conditioner')}
      </Alert>
    ) : (
      <>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box>
            <Typography variant="body1" color="text.primary">
              {t('settingsCards.enableNightBoost')}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {t('settingsCards.enableNightBoostDescription')}
            </Typography>
          </Box>
          <Switch
            checked={area.night_boost_enabled ?? true}
            onChange={e =>
              updateNightBoost(area.id, { night_boost_enabled: e.target.checked }, onUpdate)
            }
          />
        </Box>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          {t('settingsCards.nightBoostPeriod')}
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
          <TextField
            label={t('settingsCards.startTime')}
            type="time"
            value={area.night_boost_start_time ?? '22:00'}
            data-testid="night-boost-start-time-input"
            onChange={e =>
              updateNightBoost(area.id, { night_boost_start_time: e.target.value }, onUpdate)
            }
            disabled={!area.night_boost_enabled}
            slotProps={{ inputLabel: { shrink: true }, htmlInput: { step: 300 } }}
            sx={{ flex: 1 }}
          />
          <TextField
            label={t('settingsCards.endTime')}
            type="time"
            value={area.night_boost_end_time ?? '06:00'}
            data-testid="night-boost-end-time-input"
            onChange={e =>
              updateNightBoost(area.id, { night_boost_end_time: e.target.value }, onUpdate)
            }
            disabled={!area.night_boost_enabled}
            slotProps={{ inputLabel: { shrink: true }, htmlInput: { step: 300 } }}
            sx={{ flex: 1 }}
          />
        </Box>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          {t('settingsCards.nightBoostOffset')}
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Slider
            value={area.night_boost_offset ?? 0.5}
            onChange={(_e, value) =>
              updateNightBoost(area.id, { night_boost_offset: value }, onUpdate)
            }
            min={0}
            max={3}
            step={0.1}
            marks={[
              { value: 0, label: '0°C' },
              { value: 1.5, label: '1.5°C' },
              { value: 3, label: '3°C' },
            ]}
            valueLabelDisplay="auto"
            valueLabelFormat={value => `+${value}°C`}
            disabled={!area.night_boost_enabled}
            sx={{ flexGrow: 1 }}
          />
          <Typography variant="h6" color="primary" sx={{ minWidth: 60 }}>
            +{area.night_boost_offset ?? 0.5}°C
          </Typography>
        </Box>
      </>
    ),
})
