import { FormControl, InputLabel, Select, MenuItem, Alert } from '@mui/material'
import BookmarkIcon from '@mui/icons-material/Bookmark'
import { TFunction } from 'i18next'
import { Zone, GlobalPresets } from '../../types'
import { SettingSection } from '../DraggableSettings'
import { isEnabledVal, getPresetTemp } from '../../utils/areaHelpers'
import { setPresetMode } from '../../api/areas'

export interface PresetModesSectionProps {
  area: Zone
  globalPresets: GlobalPresets | null
  onUpdate: () => void
  t: TFunction
}

export const PresetModesSection = ({
  area,
  globalPresets,
  onUpdate,
  t,
}: PresetModesSectionProps): SettingSection => {
  const areaEnabled = isEnabledVal(area.enabled)

  return {
    id: 'preset-modes',
    title: t('settingsCards.presetModesTitle'),
    description: t('settingsCards.presetModesDescription'),
    icon: <BookmarkIcon />,
    badge:
      !areaEnabled || area.state === 'off' || area.preset_mode === 'none'
        ? undefined
        : t(`presets.${area.preset_mode}`),
    defaultExpanded: false,
    content: (
      <>
        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel>{t('settingsCards.currentPreset')}</InputLabel>
          <Select
            data-testid="preset-mode-select"
            disabled={!areaEnabled || area.state === 'off'}
            value={
              ['none', 'away', 'eco', 'comfort', 'home', 'sleep', 'activity', 'boost'].includes(
                area.preset_mode || '',
              )
                ? area.preset_mode
                : ''
            }
            label={t('settingsCards.currentPreset')}
            onChange={async e => {
              try {
                await setPresetMode(area.id, e.target.value)
                onUpdate()
              } catch (error) {
                console.error('Failed to set preset mode:', error)
              }
            }}
          >
            <MenuItem value="none">{t('settingsCards.presetNoneManual')}</MenuItem>
            <MenuItem value="away">
              {t('settingsCards.presetAwayTemp', {
                temp: getPresetTemp(area, globalPresets, 'away', area.away_temp, 16),
              })}
            </MenuItem>
            <MenuItem value="eco">
              {t('settingsCards.presetEcoTemp', {
                temp: getPresetTemp(area, globalPresets, 'eco', area.eco_temp, 18),
              })}
            </MenuItem>
            <MenuItem value="comfort">
              {t('settingsCards.presetComfortTemp', {
                temp: getPresetTemp(area, globalPresets, 'comfort', area.comfort_temp, 22),
              })}
            </MenuItem>
            <MenuItem value="home">
              {t('settingsCards.presetHomeTemp', {
                temp: getPresetTemp(area, globalPresets, 'home', area.home_temp, 21),
              })}
            </MenuItem>
            <MenuItem value="sleep">
              {t('settingsCards.presetSleepTemp', {
                temp: getPresetTemp(area, globalPresets, 'sleep', area.sleep_temp, 19),
              })}
            </MenuItem>
            <MenuItem value="activity">
              {t('settingsCards.presetActivityTemp', {
                temp: getPresetTemp(area, globalPresets, 'activity', area.activity_temp, 23),
              })}
            </MenuItem>
            <MenuItem value="boost">{t('settingsCards.presetBoost')}</MenuItem>
            {area.preset_mode &&
              !['none', 'away', 'eco', 'comfort', 'home', 'sleep', 'activity', 'boost'].includes(
                area.preset_mode,
              ) && (
                <MenuItem value={area.preset_mode}>
                  {t(`presets.${area.preset_mode}`, { defaultValue: area.preset_mode })}
                </MenuItem>
              )}
          </Select>
        </FormControl>

        {areaEnabled && area.state !== 'off' && (
          <Alert severity="info">
            {t('settingsCards.currentPresetInfo', {
              preset: t(`presets.${area.preset_mode || 'none'}`),
            })}
          </Alert>
        )}
      </>
    ),
  }
}
