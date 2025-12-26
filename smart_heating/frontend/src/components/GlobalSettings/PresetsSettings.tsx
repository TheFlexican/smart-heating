import React from 'react'
import { Box, Typography, Paper, Stack, Slider } from '@mui/material'
import { useTranslation } from 'react-i18next'

export interface GlobalPresetsData {
  away_temp: number
  eco_temp: number
  comfort_temp: number
  home_temp: number
  sleep_temp: number
  activity_temp: number
}

const presetLabels: Record<keyof GlobalPresetsData, string> = {
  away_temp: 'Away',
  eco_temp: 'Eco',
  comfort_temp: 'Comfort',
  home_temp: 'Home',
  sleep_temp: 'Sleep',
  activity_temp: 'Activity',
}

const presetDescriptions: Record<keyof GlobalPresetsData, string> = {
  away_temp: 'Used when nobody is home',
  eco_temp: 'Energy-saving temperature',
  comfort_temp: 'Comfortable temperature for relaxing',
  home_temp: 'Standard temperature when home',
  sleep_temp: 'Nighttime sleeping temperature',
  activity_temp: 'Active daytime temperature',
}

export const PresetsSettings: React.FC<{
  presets: GlobalPresetsData
  saving: boolean
  onChange: (key: keyof GlobalPresetsData, value: number) => void
  onCommit: (key: keyof GlobalPresetsData, value: number) => void
}> = ({ presets, saving, onChange, onCommit }) => {
  const { t } = useTranslation()

  return (
    <Paper sx={{ p: { xs: 2, sm: 3, md: 4 }, mb: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>
          {t('globalSettings.presets.title', 'Preset Temperatures')}
        </Typography>
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        {t(
          'globalSettings.presets.description',
          'These are the default temperatures for each preset mode. Areas can choose to use these global settings or define their own custom temperatures.',
        )}
      </Typography>

      <Stack spacing={3}>
        {Object.entries(presetLabels).map(([key, label]) => {
          const presetKey = key as keyof GlobalPresetsData
          const value = presets[presetKey]

          return (
            <Box key={key}>
              <Typography variant="subtitle1" sx={{ mb: 0.5 }}>
                {label}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {presetDescriptions[presetKey]}
              </Typography>

              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, px: 1 }}>
                <Slider
                  data-testid={`global-preset-${presetKey.replace('_temp', '')}-slider`}
                  value={value}
                  onChange={(_, newValue) => onChange(presetKey, newValue)}
                  onChangeCommitted={(_e, newValue) => onCommit(presetKey, newValue)}
                  min={5}
                  max={30}
                  step={0.1}
                  marks={[
                    { value: 5, label: '5°C' },
                    { value: 15, label: '15°C' },
                    { value: 20, label: '20°C' },
                    { value: 25, label: '25°C' },
                    { value: 30, label: '30°C' },
                  ]}
                  valueLabelDisplay="auto"
                  valueLabelFormat={v => `${v}°C`}
                  disabled={saving}
                  sx={{ maxWidth: 600 }}
                />
              </Box>
            </Box>
          )
        })}
      </Stack>

      <Typography variant="body2" color="text.secondary" sx={{ mt: 3, fontStyle: 'italic' }}>
        💡{' '}
        {t(
          'globalSettings.presets.tip',
          'Tip: To customize temperatures for a specific area, go to that area\'s settings and toggle off "Use global preset" for individual preset modes.',
        )}
      </Typography>
    </Paper>
  )
}
