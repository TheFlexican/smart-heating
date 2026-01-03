import { Alert, Box, FormControlLabel, Slider, Switch, Typography } from '@mui/material'
import TuneIcon from '@mui/icons-material/Tune'
import { Zone } from '../../types'
import { SettingSection } from '../DraggableSettings'
import { setAreaHysteresis } from '../../api/areas'

export interface HeatingControlSectionProps {
  area: Zone
  onUpdate: () => void
  t: (key: string, options?: any) => string
}

export const HeatingControlSection = ({
  area,
  onUpdate,
  t,
}: HeatingControlSectionProps): SettingSection => {
  return {
    id: 'heating-control',
    title: t('settingsCards.heatingControlTitle'),
    description:
      area.heating_type === 'airco'
        ? t('settingsCards.disabledForAirco')
        : t('settingsCards.heatingControlDescription'),
    icon: <TuneIcon />,
    defaultExpanded: false,
    content:
      area.heating_type === 'airco' ? (
        <Alert severity="info" data-testid="heating-control-disabled-airco">
          {t('settingsCards.disabledForAirco')}
        </Alert>
      ) : (
        <>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            {t('settingsCards.temperatureHysteresis')}
          </Typography>
          <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
            {t('settingsCards.temperatureHysteresisDescription')}
          </Typography>

          <FormControlLabel
            control={
              <Switch
                checked={
                  area.hysteresis_override === null || area.hysteresis_override === undefined
                }
                onChange={async e => {
                  const useGlobal = e.target.checked

                  try {
                    await setAreaHysteresis(area.id, {
                      use_global: useGlobal,
                      hysteresis: useGlobal ? null : 0.5,
                    })
                    onUpdate()
                  } catch (error) {
                    console.error('Failed to update hysteresis setting:', error)
                  }
                }}
              />
            }
            label={t('settingsCards.useGlobalHysteresis')}
            sx={{ mb: 2 }}
          />

          {area.hysteresis_override === null || area.hysteresis_override === undefined ? (
            <Alert severity="info" sx={{ mb: 2 }}>
              {t('settingsCards.usingGlobalHysteresis')}
            </Alert>
          ) : (
            <>
              <Alert severity="warning" sx={{ mb: 2 }}>
                {t('settingsCards.usingAreaHysteresis')}
              </Alert>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 4 }}>
                <Slider
                  value={area.hysteresis_override || 0.5}
                  onChange={async (_e, value) => {
                    try {
                      await setAreaHysteresis(area.id, {
                        use_global: false,
                        hysteresis: value,
                      })
                      onUpdate()
                    } catch (error) {
                      console.error('Failed to update hysteresis:', error)
                    }
                  }}
                  min={0.1}
                  max={2}
                  step={0.1}
                  marks={[
                    { value: 0.1, label: '0.1°C' },
                    { value: 1, label: '1.0°C' },
                    { value: 2, label: '2.0°C' },
                  ]}
                  valueLabelDisplay="on"
                  valueLabelFormat={value => `${value}°C`}
                  sx={{ flexGrow: 1 }}
                />
              </Box>
            </>
          )}

          <Typography variant="body2" color="text.secondary" gutterBottom>
            {t('settingsCards.temperatureLimits')}
          </Typography>
          <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
            {t('settingsCards.temperatureLimitsDescription')}
          </Typography>
          <Box sx={{ display: 'flex', gap: 3 }}>
            <Box sx={{ flex: 1 }}>
              <Typography variant="caption" color="text.secondary">
                {t('settingsCards.minimumTemperature')}
              </Typography>
              <Typography variant="h4" color="text.primary">
                5°C
              </Typography>
            </Box>
            <Box sx={{ flex: 1 }}>
              <Typography variant="caption" color="text.secondary">
                {t('settingsCards.maximumTemperature')}
              </Typography>
              <Typography variant="h4" color="text.primary">
                30°C
              </Typography>
            </Box>
          </Box>
        </>
      ),
  }
}
