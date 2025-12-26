import { Box, Typography, FormControlLabel, Switch, Slider, Alert } from '@mui/material'
import BookmarkIcon from '@mui/icons-material/Bookmark'
import { TFunction } from 'i18next'
import { Zone, GlobalPresets } from '../../types'
import { SettingSection } from '../DraggableSettings'
import { setAreaPresetConfig } from '../../api/areas'

export interface PresetConfigSectionProps {
  area: Zone
  globalPresets: GlobalPresets | null
  onUpdate: () => void
  t: TFunction
}

export const PresetConfigSection = ({
  area,
  globalPresets,
  onUpdate,
  t,
}: PresetConfigSectionProps): SettingSection => {
  return {
    id: 'preset-config',
    title: t('settingsCards.presetTemperatureConfigTitle'),
    description: t('settingsCards.presetTemperatureConfigDescription'),
    icon: <BookmarkIcon />,
    defaultExpanded: false,
    content: (
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {globalPresets &&
          [
            {
              key: 'away',
              label: 'Away',
              global: globalPresets.away_temp,
              custom: area.away_temp,
            },
            { key: 'eco', label: 'Eco', global: globalPresets.eco_temp, custom: area.eco_temp },
            {
              key: 'comfort',
              label: 'Comfort',
              global: globalPresets.comfort_temp,
              custom: area.comfort_temp,
            },
            {
              key: 'home',
              label: 'Home',
              global: globalPresets.home_temp,
              custom: area.home_temp,
            },
            {
              key: 'sleep',
              label: 'Sleep',
              global: globalPresets.sleep_temp,
              custom: area.sleep_temp,
            },
            {
              key: 'activity',
              label: 'Activity',
              global: globalPresets.activity_temp,
              custom: area.activity_temp,
            },
          ].map(preset => {
            const useGlobalKey = `use_global_${preset.key}` as keyof Zone
            const useGlobal = (area[useGlobalKey] as boolean | undefined) ?? true
            const effectiveTemp = useGlobal ? preset.global : preset.custom

            return (
              <Box key={preset.key}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={useGlobal}
                      onChange={async e => {
                        e.stopPropagation()
                        try {
                          await setAreaPresetConfig(area.id, { [useGlobalKey]: e.target.checked })
                          await onUpdate()
                        } catch (error) {
                          console.error('Failed to update preset config:', error)
                          alert(`Failed to update preset: ${error}`)
                        }
                      }}
                    />
                  }
                  label={
                    <Box>
                      <Typography variant="body1">
                        {useGlobal
                          ? t('settingsCards.presetUseGlobal', { preset: preset.label })
                          : t('settingsCards.presetUseCustom', { preset: preset.label })}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {useGlobal
                          ? t('settingsCards.usingGlobalSetting', { temp: preset.global })
                          : t('settingsCards.usingCustomSetting', {
                              temp: preset.custom ?? 'not set',
                            })}
                      </Typography>
                    </Box>
                  }
                />
                {!useGlobal && (
                  <Box sx={{ mt: 2, pl: 2 }}>
                    <Typography variant="body2" gutterBottom>
                      {t('settingsCards.customTemperature')}:{' '}
                      {preset.custom?.toFixed(1) ?? effectiveTemp?.toFixed(1)}°C
                    </Typography>
                    <Slider
                      value={preset.custom ?? effectiveTemp ?? 20}
                      min={10}
                      max={30}
                      step={0.5}
                      marks={[
                        { value: 15, label: '15°C' },
                        { value: 20, label: '20°C' },
                        { value: 25, label: '25°C' },
                      ]}
                      valueLabelDisplay="auto"
                      onChange={async (_, newValue) => {
                        try {
                          await setAreaPresetConfig(area.id, {
                            [`${preset.key}_temp`]: newValue as number,
                          })
                          await onUpdate()
                        } catch (error) {
                          console.error('Failed to update custom temperature:', error)
                          alert(`Failed to update temperature: ${error}`)
                        }
                      }}
                    />
                  </Box>
                )}
              </Box>
            )
          })}
        <Alert severity="info" sx={{ mt: 2 }}>
          {t('settingsCards.presetConfigInfo')}
        </Alert>
      </Box>
    ),
  }
}
