import React from 'react'
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  FormControlLabel,
  Switch,
  Typography,
  Slider,
} from '@mui/material'
import { Zone, GlobalPresets } from '../../types'
import { useTranslation } from 'react-i18next'
import { setPresetMode, setAreaPresetConfig } from '../../api/areas'

interface Props {
  area: Zone
  areaEnabled: boolean
  globalPresets: GlobalPresets | null
  getPresetTemp: (presetKey: string, custom: number | undefined, fallback: number) => string
  loadData: () => Promise<void>
}

const PresetControls: React.FC<Props> = ({
  area,
  areaEnabled,
  globalPresets,
  getPresetTemp,
  loadData,
}) => {
  const { t } = useTranslation()

  return (
    <>
      <FormControl fullWidth sx={{ mb: 2 }}>
        <InputLabel>{t('settingsCards.currentPreset')}</InputLabel>
        <Select
          data-testid="preset-mode-select"
          disabled={!areaEnabled || area.state === 'off'}
          value={area.preset_mode || 'none'}
          label={t('settingsCards.currentPreset')}
          onChange={async e => {
            try {
              await setPresetMode(area.id, e.target.value)
              await loadData()
            } catch (error) {
              console.error('Failed to set preset mode:', error)
            }
          }}
        >
          <MenuItem value="none">{t('settingsCards.presetNoneManual')}</MenuItem>
          <MenuItem value="away">
            {t('settingsCards.presetAwayTemp', {
              temp: getPresetTemp('away', area.away_temp, 16),
            })}
          </MenuItem>
          <MenuItem value="eco">
            {t('settingsCards.presetEcoTemp', {
              temp: getPresetTemp('eco', area.eco_temp, 18),
            })}
          </MenuItem>
          <MenuItem value="comfort">
            {t('settingsCards.presetComfortTemp', {
              temp: getPresetTemp('comfort', area.comfort_temp, 22),
            })}
          </MenuItem>
          <MenuItem value="home">
            {t('settingsCards.presetHomeTemp', {
              temp: getPresetTemp('home', area.home_temp, 21),
            })}
          </MenuItem>
          <MenuItem value="sleep">
            {t('settingsCards.presetSleepTemp', {
              temp: getPresetTemp('sleep', area.sleep_temp, 19),
            })}
          </MenuItem>
          <MenuItem value="activity">
            {t('settingsCards.presetActivityTemp', {
              temp: getPresetTemp('activity', area.activity_temp, 23),
            })}
          </MenuItem>
          <MenuItem value="boost">{t('settingsCards.presetBoost')}</MenuItem>
        </Select>
      </FormControl>

      {areaEnabled && area.state !== 'off' && (
        <Alert severity="info">
          {t('settingsCards.currentPresetInfo', {
            preset: t(`presets.${area.preset_mode || 'none'}`),
          })}
        </Alert>
      )}

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
        {globalPresets &&
          [
            { key: 'away', label: 'Away', global: globalPresets.away_temp, custom: area.away_temp },
            { key: 'eco', label: 'Eco', global: globalPresets.eco_temp, custom: area.eco_temp },
            {
              key: 'comfort',
              label: 'Comfort',
              global: globalPresets.comfort_temp,
              custom: area.comfort_temp,
            },
            { key: 'home', label: 'Home', global: globalPresets.home_temp, custom: area.home_temp },
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
                        const newValue = e.target.checked
                        try {
                          await setAreaPresetConfig(area.id, { [useGlobalKey]: newValue })
                          await loadData()
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
                        const tempValue = newValue as number
                        const tempKey = `${preset.key}_temp` as keyof Zone
                        try {
                          await setAreaPresetConfig(area.id, { [tempKey]: tempValue })
                          await loadData()
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
    </>
  )
}

export default PresetControls
