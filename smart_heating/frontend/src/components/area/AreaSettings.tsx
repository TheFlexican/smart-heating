import { useState } from 'react'
import {
  Box,
  Typography,
  Slider,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  RadioGroup,
  Radio,
  TextField,
  Alert,
} from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Zone, GlobalPresets } from '../../types'
import PresetControls from '../common/PresetControls'
import BoostControls from '../common/BoostControls'
import AutoPresetControls from '../global/AutoPresetControls'
import OutdoorSensorControls from './OutdoorSensorControls'
import SensorConfigControls from './SensorConfigControls'
import HistoryMigrationControls from './HistoryMigrationControls'
import StorageBackendInfo from '../common/StorageBackendInfo'
import DraggableSettings, { SettingSection } from '../common/DraggableSettings'
import {
  setAreaPresetConfig,
  setHvacMode,
  setSwitchShutdown,
  setAreaHeatingCurve,
} from '../../api/areas'
import { setAreaPresenceConfig } from '../../api/sensors'
import { migrateHistoryStorage } from '../../api/history'

interface Props {
  area: Zone
  globalPresets: GlobalPresets | null
  entityStates: Record<string, any>
  loadData: () => Promise<void>
  storageBackend: string
  databaseStats: any
  migrating: boolean
  setMigrating: (v: boolean) => void
  historyRetention: number
  recordInterval: number
  loadHistoryConfig: () => Promise<void>
}

export default function AreaSettings(props: Readonly<Props>) {
  const { t } = useTranslation()
  const {
    area,
    globalPresets,
    entityStates,
    loadData,
    storageBackend,
    databaseStats,
    migrating,
    setMigrating,
    historyRetention,
    recordInterval,
    loadHistoryConfig,
  } = props
  const [expandedCard, setExpandedCard] = useState<string | null>(null)

  const getPresetTemp = (
    presetKey: string,
    customTemp: number | undefined,
    fallback: number,
  ): string => {
    const useGlobalKey = `use_global_${presetKey}` as keyof Zone
    const useGlobal = (area[useGlobalKey] as boolean | undefined) ?? true
    if (useGlobal && globalPresets) {
      const globalKey = `${presetKey}_temp` as keyof GlobalPresets
      return `${(globalPresets as any)[globalKey]}°C (global)`
    }
    return `${customTemp ?? fallback}°C (custom)`
  }

  // History migration handlers extracted to keep JSX attributes small

  const sections: SettingSection[] = [
    {
      id: 'preset-modes',
      title: t('settingsCards.presetModesTitle'),
      description: t('settingsCards.presetModesDescription'),
      icon: null,
      badge: undefined,
      defaultExpanded: false,
      content: (
        <PresetControls
          area={area}
          areaEnabled={!!area.enabled}
          globalPresets={globalPresets}
          getPresetTemp={getPresetTemp}
          loadData={loadData}
        />
      ),
    },
    {
      id: 'preset-config',
      title: t('settingsCards.presetTemperatureConfigTitle'),
      description: t('settingsCards.presetTemperatureConfigDescription'),
      icon: null,
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
                          const newValue = e.target.checked
                          try {
                            await setAreaPresetConfig(area.id, { [useGlobalKey]: newValue } as any)
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
                        onChange={async (_e, newValue) => {
                          const tempValue = Number(newValue)
                          const tempKey = `${preset.key}_temp` as keyof Zone
                          try {
                            await setAreaPresetConfig(area.id, { [tempKey]: tempValue } as any)
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
      ),
    },
    {
      id: 'boost-mode',
      title: t('settingsCards.boostModeTitle'),
      description:
        area.heating_type === 'airco'
          ? t('settingsCards.disabledForAirco')
          : t('settingsCards.boostModeDescription'),
      icon: null,
      badge: area.boost_mode_active ? 'ACTIVE' : undefined,
      defaultExpanded: area.boost_mode_active,
      content: <BoostControls area={area} loadData={loadData} />,
    },
    {
      id: 'hvac-mode',
      title: 'HVAC Mode',
      description: 'Control the heating/cooling mode for this area',
      icon: null,
      defaultExpanded: false,
      content: (
        <FormControl fullWidth>
          <InputLabel>HVAC Mode</InputLabel>
          <Select
            value={area.hvac_mode || 'heat'}
            label="HVAC Mode"
            onChange={async e => {
              try {
                await setHvacMode(area.id, e.target.value)
                loadData()
              } catch (error) {
                console.error('Failed to set HVAC mode:', error)
              }
            }}
          >
            <MenuItem value="heat">Heat</MenuItem>
            <MenuItem value="cool">Cool</MenuItem>
            <MenuItem value="auto">Auto</MenuItem>
            <MenuItem value="off">Off</MenuItem>
          </Select>
        </FormControl>
      ),
    },
    {
      id: 'heating-type',
      title: t('settingsCards.heatingTypeTitle', 'Heating Type'),
      description: t('settingsCards.heatingTypeDescription'),
      icon: null,
      defaultExpanded: false,
      content: (
        <Box>
          <RadioGroup
            aria-label={t('settingsCards.heatingTypeTitle')}
            value={area.heating_type || 'radiator'}
            onChange={async _e => {
              try {
                await setAreaHeatingCurve(
                  area.id,
                  (area.heating_curve_coefficient as any) ?? undefined,
                )
                await loadData()
              } catch (error) {
                console.error('Failed to update heating type:', error)
              }
            }}
          >
            <FormControlLabel
              value="radiator"
              control={<Radio />}
              label={
                <Box>
                  <Typography variant="body1">{t('settingsCards.radiator', 'Radiator')}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {t('settingsCards.radiatorDescription')}
                  </Typography>
                </Box>
              }
            />
            <FormControlLabel
              value="floor_heating"
              control={<Radio />}
              label={
                <Box>
                  <Typography variant="body1">
                    {t('settingsCards.floorHeating', 'Floor Heating')}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {t('settingsCards.floorHeatingDescription')}
                  </Typography>
                </Box>
              }
            />
            <FormControlLabel
              value="airco"
              control={<Radio />}
              label={
                <Box>
                  <Typography variant="body1">
                    {t('settingsCards.airConditioner', 'Air Conditioner')}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {t('settingsCards.aircoDescription')}
                  </Typography>
                </Box>
              }
            />
          </RadioGroup>
          <Alert severity="info" sx={{ mt: 2 }}>
            {t('settingsCards.heatingTypeInfo')}
          </Alert>
        </Box>
      ),
    },
    {
      id: 'switch-control',
      title: t('settingsCards.switchPumpControlTitle'),
      description: t('settingsCards.switchPumpControlDescription'),
      icon: null,
      defaultExpanded: false,
      content: (
        <Box>
          <FormControlLabel
            control={
              <Switch
                checked={area.shutdown_switches_when_idle ?? true}
                disabled={area.heating_type === 'airco'}
                onChange={async e => {
                  try {
                    await setSwitchShutdown(area.id, e.target.checked)
                    loadData()
                  } catch (error) {
                    console.error('Failed to update switch shutdown setting:', error)
                  }
                }}
              />
            }
            label={t('settingsCards.shutdownSwitchesPumps')}
          />
          <Typography
            variant="caption"
            color="text.secondary"
            display="block"
            sx={{ mt: 1, ml: 4 }}
          >
            {area.heating_type === 'airco'
              ? t('settingsCards.disabledForAirco')
              : t('settingsCards.shutdownSwitchesDescription')}
          </Typography>
        </Box>
      ),
    },
    {
      id: 'window-sensors',
      title: t('settingsCards.windowSensorsTitle'),
      description: t('settingsCards.windowSensorsDescription'),
      icon: null,
      badge: area.window_sensors?.length || undefined,
      defaultExpanded: false,
      content: <SensorConfigControls area={area} entityStates={entityStates} loadData={loadData} />,
    },
    {
      id: 'presence-config',
      title: t('settingsCards.presenceConfigTitle'),
      description: t('settingsCards.presenceConfigDescription'),
      icon: null,
      defaultExpanded: false,
      content: (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <FormControlLabel
            control={
              <Switch
                checked={area.use_global_presence ?? false}
                onChange={async e => {
                  e.stopPropagation()
                  const newValue = e.target.checked
                  try {
                    await setAreaPresenceConfig(area.id, newValue)
                    await loadData()
                  } catch (error) {
                    console.error('Failed to update presence config:', error)
                    alert(`Failed to update presence config: ${error}`)
                  }
                }}
              />
            }
            label={
              <Box>
                <Typography variant="body1">
                  {area.use_global_presence
                    ? t('settingsCards.useGlobalPresence')
                    : t('settingsCards.useAreaSpecificSensors')}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {area.use_global_presence
                    ? t('settingsCards.useGlobalPresenceDescription')
                    : t('settingsCards.useAreaSpecificDescription')}
                </Typography>
              </Box>
            }
          />
          <Alert severity="info">{t('settingsCards.presenceToggleInfo')}</Alert>
        </Box>
      ),
    },
    {
      id: 'auto-preset',
      title: t('settingsCards.autoPresetTitle'),
      description: t('settingsCards.autoPresetDescription'),
      icon: null,
      badge: area.auto_preset_enabled ? 'AUTO' : 'OFF',
      defaultExpanded: false,
      content: (
        <>
          <Box
            sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}
          >
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
                  await fetch(`/api/smart_heating/areas/${area.id}/auto_preset`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ auto_preset_enabled: e.target.checked }),
                  })
                  loadData()
                } catch (error) {
                  console.error('Failed to update auto preset:', error)
                }
              }}
            />
          </Box>
          <AutoPresetControls area={area} loadData={loadData} />
        </>
      ),
    },
    {
      id: 'night-boost',
      title: t('settingsCards.nightBoostTitle'),
      description:
        area.heating_type === 'airco'
          ? t('settingsCards.disabledForAirco')
          : t('settingsCards.nightBoostDescription'),
      icon: null,
      badge: area.night_boost_enabled ? 'ON' : 'OFF',
      defaultExpanded: false,
      content:
        area.heating_type === 'airco' ? (
          <Alert severity="info" data-testid="night-boost-disabled-airco">
            {t('settingsCards.disabledForAirco')}
          </Alert>
        ) : (
          <>
            <Box
              sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}
            >
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
                onChange={async e => {
                  try {
                    await fetch('/api/smart_heating/call_service', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        service: 'set_night_boost',
                        area_id: area.id,
                        night_boost_enabled: e.target.checked,
                      }),
                    })
                    loadData()
                  } catch (error) {
                    console.error('Failed to update night boost:', error)
                  }
                }}
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
                onChange={async e => {
                  try {
                    await fetch('/api/smart_heating/call_service', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        service: 'set_night_boost',
                        area_id: area.id,
                        night_boost_start_time: e.target.value,
                      }),
                    })
                    await loadData()
                  } catch (error) {
                    console.error('Failed to update night boost start time:', error)
                  }
                }}
                disabled={!area.night_boost_enabled}
                slotProps={{ inputLabel: { shrink: true }, htmlInput: { step: 300 } }}
                sx={{ flex: 1 }}
              />
              <TextField
                label={t('settingsCards.endTime')}
                type="time"
                value={area.night_boost_end_time ?? '06:00'}
                data-testid="night-boost-end-time-input"
                onChange={async e => {
                  try {
                    await fetch('/api/smart_heating/call_service', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        service: 'set_night_boost',
                        area_id: area.id,
                        night_boost_end_time: e.target.value,
                      }),
                    })
                    await loadData()
                  } catch (error) {
                    console.error('Failed to update night boost end time:', error)
                  }
                }}
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
                onChange={async (_e, value) => {
                  try {
                    await fetch('/api/smart_heating/call_service', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        service: 'set_night_boost',
                        area_id: area.id,
                        night_boost_offset: value,
                      }),
                    })
                    await loadData()
                  } catch (error) {
                    console.error('Failed to update night boost offset:', error)
                  }
                }}
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
    },
    {
      id: 'smart-night-boost',
      title: t('settingsCards.smartNightBoostTitle'),
      description:
        area.heating_type === 'airco'
          ? t('settingsCards.disabledForAirco')
          : t('settingsCards.smartNightBoostDescription'),
      icon: null,
      badge: area.smart_boost_enabled ? 'LEARNING' : 'OFF',
      defaultExpanded: false,
      content:
        area.heating_type === 'airco' ? (
          <Alert severity="info" data-testid="smart-night-boost-disabled-airco">
            {t('settingsCards.disabledForAirco')}
          </Alert>
        ) : (
          <>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              {t('settingsCards.smartNightBoostIntro')}
            </Typography>
            <Box
              sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}
            >
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
                onChange={async e => {
                  try {
                    await fetch('/api/smart_heating/call_service', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        service: 'set_night_boost',
                        area_id: area.id,
                        smart_boost_enabled: e.target.checked,
                      }),
                    })
                    await loadData()
                  } catch (error) {
                    console.error('Failed to update smart night boost:', error)
                  }
                }}
              />
            </Box>
            <TextField
              label={t('settingsCards.targetWakeupTime')}
              type="time"
              value={area.smart_boost_target_time ?? '06:00'}
              data-testid="smart-night-boost-target-time-input"
              onChange={async e => {
                try {
                  await fetch('/api/smart_heating/call_service', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                      service: 'set_night_boost',
                      area_id: area.id,
                      smart_boost_target_time: e.target.value,
                    }),
                  })
                  await loadData()
                } catch (error) {
                  console.error('Failed to update target time:', error)
                }
              }}
              disabled={!area.smart_boost_enabled}
              fullWidth
              helperText={t('settingsCards.targetWakeupTimeHelper')}
              slotProps={{ inputLabel: { shrink: true }, htmlInput: { step: 300 } }}
              sx={{ mb: 3 }}
            />
            <OutdoorSensorControls area={area} loadData={loadData} />
            {area.smart_boost_enabled && (
              <Box sx={{ mt: 3, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
                <Typography variant="body2" color="info.dark">
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
    },
    {
      id: 'heating-control',
      title: t('settingsCards.heatingControlTitle'),
      description:
        area.heating_type === 'airco'
          ? t('settingsCards.disabledForAirco')
          : t('settingsCards.heatingControlDescription'),
      icon: null,
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
                      const response = await fetch(
                        `/api/smart_heating/areas/${area.id}/hysteresis`,
                        {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({
                            use_global: useGlobal,
                            hysteresis: useGlobal ? null : 0.5,
                          }),
                        },
                      )
                      if (!response.ok) {
                        const errorText = await response.text()
                        console.error('Failed to update hysteresis setting:', errorText)
                      }
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
                        const response = await fetch(
                          `/api/smart_heating/areas/${area.id}/hysteresis`,
                          {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ use_global: false, hysteresis: value }),
                          },
                        )
                        if (!response.ok) {
                          const errorText = await response.text()
                          console.error('Failed to update hysteresis:', errorText)
                        }
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
    },
    {
      id: 'history-management',
      title: t('settingsCards.historyManagementTitle'),
      description: t('settingsCards.historyManagementDescription'),
      icon: null,
      defaultExpanded: false,
      content: (
        <>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            {t('settingsCards.dataRetentionDescription', { interval: recordInterval })}
          </Typography>
          <StorageBackendInfo
            storageBackend={storageBackend as any}
            databaseStats={databaseStats}
          />
          <Box sx={{ mb: 0 }}>
            <HistoryMigrationControls
              storageBackend={storageBackend as any}
              migrating={migrating}
              onMigrateToDatabase={handleMigrateToDatabase}
              onMigrateToJson={handleMigrateToJson}
            />
          </Box>
          <Alert severity="info" sx={{ mt: 2 }} icon={false}>
            <Typography variant="caption">
              <strong>Database storage</strong> requires MariaDB ≥10.3, MySQL ≥8.0, or PostgreSQL
              ≥12. SQLite is not supported and will automatically fall back to JSON storage.
            </Typography>
          </Alert>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            {t('settingsCards.dataRetentionPeriod', { days: historyRetention })}
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mt: 2, mb: 3 }}>
            <Slider
              value={historyRetention}
              onChange={(_, _value) => {
                /* handled in parent */
              }}
              min={1}
              max={365}
              step={1}
              marks={[
                { value: 1, label: '1d' },
                { value: 30, label: '30d' },
                { value: 90, label: '90d' },
                { value: 180, label: '180d' },
                { value: 365, label: '365d' },
              ]}
              valueLabelDisplay="auto"
              valueLabelFormat={value => `${value}d`}
              sx={{ flexGrow: 1 }}
            />
            <Button
              variant="contained"
              size="small"
              onClick={async () => {
                try {
                  /* parent should provide update */ await loadHistoryConfig()
                } catch (error) {
                  console.error('Failed to update history retention:', error)
                }
              }}
            >
              {t('common.save')}
            </Button>
          </Box>
          <Alert severity="info" sx={{ mt: 2 }}>
            <strong>Note:</strong> {t('settingsCards.historyNote', { interval: recordInterval })}
          </Alert>
        </>
      ),
    },
  ]

  // History migration handlers extracted to keep JSX attributes small
  async function handleMigrateToDatabase() {
    if (
      !globalThis.confirm(
        'Migrate history data to database? This requires MariaDB, MySQL, or PostgreSQL. SQLite is not supported.',
      )
    )
      return
    setMigrating(true)
    try {
      const result = await migrateHistoryStorage('database')
      if (result.success) {
        alert(`Successfully migrated ${result.migrated_entries} entries to database!`)
        await loadHistoryConfig()
      } else {
        alert(`Migration failed: ${result.message}`)
      }
    } catch (error: any) {
      alert(`Migration error: ${error.message}`)
    } finally {
      setMigrating(false)
    }
  }

  async function handleMigrateToJson() {
    if (!globalThis.confirm('Migrate history data back to JSON file storage?')) return
    setMigrating(true)
    try {
      const result = await migrateHistoryStorage('json')
      if (result.success) {
        alert(`Successfully migrated ${result.migrated_entries} entries to JSON!`)
        await loadHistoryConfig()
      } else {
        alert(`Migration failed: ${result.message}`)
      }
    } catch (error: any) {
      alert(`Migration error: ${error.message}`)
    } finally {
      setMigrating(false)
    }
  }

  return (
    <Box sx={{ maxWidth: 1600, mx: 'auto', px: 2 }}>
      <DraggableSettings
        key={`settings-${area.id}-${area.presence_sensors?.length || 0}-${area.window_sensors?.length || 0}`}
        sections={sections}
        storageKey={`area-settings-order-${area.id}`}
        expandedCard={expandedCard}
        onExpandedChange={setExpandedCard}
      />
    </Box>
  )
}
