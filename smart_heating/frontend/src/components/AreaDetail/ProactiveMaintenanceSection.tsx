import { Box, Switch, Typography, Alert, Slider, TextField } from '@mui/material'
import { useState, useEffect } from 'react'
import ThermostatAutoIcon from '@mui/icons-material/ThermostatAuto'
import { TFunction } from 'i18next'
import { Zone } from '../../types'
import { SettingSection } from '../DraggableSettings'
import { setNightBoostConfig } from '../../api/areas'

const updateProactiveMaintenance = async (
  areaId: string,
  data: Record<string, unknown>,
  onUpdate: () => void,
) => {
  try {
    await setNightBoostConfig(areaId, data)
    await new Promise(resolve => setTimeout(resolve, 500))
    onUpdate()
  } catch (error) {
    console.error('Failed to update proactive maintenance:', error)
    throw error
  }
}

const SensitivitySlider = ({
  area,
  onUpdate,
  t,
}: {
  area: Zone
  onUpdate: () => void
  t: TFunction
}) => {
  const [sliderValue, setSliderValue] = useState<number>(
    area.proactive_maintenance_sensitivity ?? 1,
  )

  useEffect(() => {
    setSliderValue(area.proactive_maintenance_sensitivity ?? 1)
  }, [area.proactive_maintenance_sensitivity])

  return (
    <Slider
      value={sliderValue}
      min={0.5}
      max={2}
      step={0.1}
      marks={[
        { value: 0.5, label: t('settingsCards.conservative', 'Conservative') },
        { value: 1, label: t('settingsCards.balanced', 'Balanced') },
        { value: 2, label: t('settingsCards.aggressive', 'Aggressive') },
      ]}
      onChange={(_, value) => setSliderValue(value as number)}
      onChangeCommitted={(_, value) =>
        updateProactiveMaintenance(
          area.id,
          { proactive_maintenance_sensitivity: value as number },
          onUpdate,
        )
      }
      valueLabelDisplay="auto"
      data-testid="proactive-maintenance-sensitivity"
    />
  )
}

export const ProactiveMaintenanceSection = ({
  area,
  onUpdate,
  t,
}: {
  area: Zone
  onUpdate: () => void
  t: TFunction
}): SettingSection => ({
  id: 'proactive-maintenance',
  title: t('settingsCards.proactiveMaintenanceTitle', 'Proactive Temperature Maintenance'),
  description:
    area.heating_type === 'airco'
      ? t('settingsCards.disabledForAirco', 'Disabled for Air Conditioner')
      : t(
          'settingsCards.proactiveMaintenanceDescription',
          'Predict temperature drops and pre-heat to maintain constant temperature',
        ),
  icon: <ThermostatAutoIcon />,
  badge: area.proactive_maintenance_enabled ? 'ACTIVE' : 'OFF',
  defaultExpanded: false,
  content:
    area.heating_type === 'airco' ? (
      <Alert severity="info" data-testid="proactive-maintenance-disabled-airco">
        {t('settingsCards.disabledForAirco', 'Disabled for Air Conditioner')}
      </Alert>
    ) : (
      <>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {t(
            'settingsCards.proactiveMaintenanceIntro',
            'Uses temperature trend analysis and learned heating data to start heating before temperature drops below target.',
          )}
        </Typography>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box>
            <Typography variant="body1" color="text.primary">
              {t('settingsCards.enableProactiveMaintenance', 'Enable Proactive Maintenance')}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {t(
                'settingsCards.enableProactiveMaintenanceDescription',
                'Maintain constant temperature by predicting drops',
              )}
            </Typography>
          </Box>
          <Switch
            checked={area.proactive_maintenance_enabled ?? false}
            onChange={e =>
              updateProactiveMaintenance(
                area.id,
                { proactive_maintenance_enabled: e.target.checked },
                onUpdate,
              )
            }
            data-testid="proactive-maintenance-toggle"
          />
        </Box>

        {area.proactive_maintenance_enabled && (
          <>
            <Box sx={{ mb: 3 }}>
              <Typography variant="body2" gutterBottom>
                {t('settingsCards.sensitivityLabel', 'Sensitivity')}
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                {t(
                  'settingsCards.sensitivityDescription',
                  'Higher sensitivity starts heating earlier. Lower is more conservative.',
                )}
              </Typography>
              <SensitivitySlider area={area} onUpdate={onUpdate} t={t} />
            </Box>

            <TextField
              label={t('settingsCards.marginMinutes', 'Safety Margin (minutes)')}
              type="number"
              defaultValue={
                area.proactive_maintenance_margin_minutes ??
                (area.heating_type === 'floor_heating' ? 15 : 5)
              }
              key={`margin-${area.proactive_maintenance_margin_minutes}`}
              onBlur={e =>
                updateProactiveMaintenance(
                  area.id,
                  { proactive_maintenance_margin_minutes: Number.parseInt(e.target.value, 10) },
                  onUpdate,
                )
              }
              fullWidth
              helperText={t(
                'settingsCards.marginMinutesHelper',
                'Extra time buffer before predicted threshold. Floor heating typically needs 15 minutes.',
              )}
              slotProps={{
                htmlInput: { min: 0, max: 60, step: 5 },
              }}
              sx={{ mb: 3 }}
              data-testid="proactive-maintenance-margin"
            />

            <TextField
              label={t('settingsCards.cooldownMinutes', 'Cooldown Period (minutes)')}
              type="number"
              defaultValue={area.proactive_maintenance_cooldown_minutes ?? 10}
              key={`cooldown-${area.proactive_maintenance_cooldown_minutes}`}
              onBlur={e =>
                updateProactiveMaintenance(
                  area.id,
                  { proactive_maintenance_cooldown_minutes: Number.parseInt(e.target.value, 10) },
                  onUpdate,
                )
              }
              fullWidth
              helperText={t(
                'settingsCards.cooldownMinutesHelper',
                'Minimum time between proactive heating sessions to prevent oscillation.',
              )}
              slotProps={{
                htmlInput: { min: 5, max: 60, step: 5 },
              }}
              sx={{ mb: 3 }}
              data-testid="proactive-maintenance-cooldown"
            />

            <TextField
              label={t('settingsCards.minTrendLabel', 'Minimum Trend Threshold (°C/hour)')}
              type="number"
              defaultValue={area.proactive_maintenance_min_trend ?? -0.1}
              key={`min-trend-${area.proactive_maintenance_min_trend}`}
              onBlur={e =>
                updateProactiveMaintenance(
                  area.id,
                  {
                    proactive_maintenance_min_trend: Number.parseFloat(e.target.value),
                  },
                  onUpdate,
                )
              }
              fullWidth
              helperText={t(
                'settingsCards.minTrendHelper',
                'Minimum temperature drop rate to trigger proactive heating. Lower values (e.g., -0.05) are more sensitive.',
              )}
              slotProps={{
                htmlInput: { min: -0.5, max: -0.01, step: 0.01 },
              }}
              sx={{ mb: 3 }}
              data-testid="proactive-maintenance-min-trend"
            />

            <Box sx={{ mt: 3, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                <strong>{t('settingsCards.howItWorksTitle', 'How it works')}</strong>
              </Typography>
              <Typography variant="caption" color="text.secondary" component="div">
                {t(
                  'settingsCards.proactiveMaintenanceBullet1',
                  'Monitors temperature trend during active schedules',
                )}
                <br />
                {t(
                  'settingsCards.proactiveMaintenanceBullet2',
                  'Predicts when temperature will drop below hysteresis threshold',
                )}
                <br />
                {t(
                  'settingsCards.proactiveMaintenanceBullet3',
                  'Uses learned heating data to estimate warmup time',
                )}
                <br />
                {t(
                  'settingsCards.proactiveMaintenanceBullet4',
                  'Starts heating early to maintain constant temperature',
                )}
              </Typography>
            </Box>

            {area.heating_type === 'floor_heating' && (
              <Alert severity="info" sx={{ mt: 2 }}>
                {t(
                  'settingsCards.floorHeatingNote',
                  'Floor heating detected. A larger safety margin is recommended due to thermal inertia.',
                )}
              </Alert>
            )}
          </>
        )}
      </>
    ),
})
