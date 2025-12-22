import { Box, Paper, Typography, Slider, Divider } from '@mui/material'
import BookmarkIcon from '@mui/icons-material/Bookmark'
import ThermostatIcon from '@mui/icons-material/Thermostat'
import { useTranslation } from 'react-i18next'
import TrvList from './TrvList'
import { Zone, TrvRuntimeState } from '../../types'

interface Props {
  area: Zone
  temperature: number
  enabled: boolean
  readonly onTemperatureChange: (e: Event, value: number | number[]) => void
  readonly onTemperatureCommit: (e: Event | React.SyntheticEvent, value: number | number[]) => Promise<void>
  readonly onOpenTrvDialog: () => void
  readonly trvs?: TrvRuntimeState[]
  readonly loadData: () => Promise<void>
}

export default function TemperatureControl({
  area,
  temperature,
  enabled,
  onTemperatureChange,
  onTemperatureCommit,
  onOpenTrvDialog,
  trvs,
  loadData,
}: Props) {
  const { t } = useTranslation()

  return (
    <Paper sx={{ p: { xs: 2, sm: 3, md: 4 }, mb: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <ThermostatIcon sx={{ fontSize: 32, color: 'primary.main' }} />
        <Typography variant="h5" color="text.primary" sx={{ fontSize: { xs: '1.1rem', sm: '1.25rem', md: '1.5rem' }, fontWeight: 600 }}>
          {t('areaDetail.temperatureControl')}
        </Typography>
      </Box>

      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.8rem', sm: '0.875rem' } }}>
          {t('areaDetail.targetTemperature')}
        </Typography>
        <Typography variant="h4" color="primary" sx={{ fontSize: { xs: '1.75rem', sm: '2.125rem' } }}>
          {temperature}°C
        </Typography>
      </Box>

      <Slider
        value={temperature}
        sx={{
          '& .MuiSlider-thumb': { width: { xs: 24, sm: 20 }, height: { xs: 24, sm: 20 } },
          '& .MuiSlider-track': { height: { xs: 6, sm: 4 } },
          '& .MuiSlider-rail': { height: { xs: 6, sm: 4 } },
        }}
        onChange={onTemperatureChange}
        onChangeCommitted={onTemperatureCommit}
        min={5}
        max={30}
        step={0.1}
        marks={[{ value: 5, label: '5°' }, { value: 15, label: '15°' }, { value: 20, label: '20°' }, { value: 25, label: '25°' }, { value: 30, label: '30°' }]}
        valueLabelDisplay="auto"
        disabled={!enabled || !!(area.preset_mode && area.preset_mode !== 'none')}
      />

      {enabled && area.state !== 'off' && area.preset_mode && area.preset_mode !== 'none' && (
        <Box mt={1} display="flex" alignItems="center" gap={1}>
          <BookmarkIcon fontSize="small" color="secondary" />
          <Typography variant="caption" color="text.secondary" dangerouslySetInnerHTML={{ __html: t('areaDetail.presetModeActive', { mode: t(`presets.${area.preset_mode}`).toUpperCase() }) }} />
        </Box>
      )}

      {area.current_temperature !== undefined && (
        <>
          <Divider sx={{ my: 3 }} />
          <Box display="flex" justifyContent="space-between">
            <Typography variant="body1" color="text.secondary">{t('areaDetail.currentTemperature')}</Typography>
            <Typography variant="h5" color="text.primary">{area.current_temperature?.toFixed(1)}°C</Typography>
          </Box>

          <TrvList area={area} trvs={trvs} onOpenAdd={onOpenTrvDialog} loadData={loadData} />
        </>
      )}
    </Paper>
  )
}
