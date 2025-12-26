import React from 'react'
import { Box, Paper, Typography, Slider, Divider } from '@mui/material'
import ThermostatIcon from '@mui/icons-material/Thermostat'
import BookmarkIcon from '@mui/icons-material/Bookmark'
import SpeedIcon from '@mui/icons-material/Speed'
import { useTranslation } from 'react-i18next'
import { Zone } from '../../types'
import { TrvList } from './TrvList'

export interface AreaOverviewTabProps {
  area: Zone
  temperature: number
  enabled: boolean
  editingTrvId: string | null
  editingTrvName: string | null
  editingTrvRole: 'position' | 'open' | 'both' | null
  onTemperatureChange: (event: Event, value: number | number[]) => void
  onTemperatureCommit: (event: Event | React.SyntheticEvent, value: number | number[]) => void
  onTrvDialogOpen: () => void
  onStartEditingTrv: (trv: any) => void
  onEditingTrvNameChange: (name: string) => void
  onEditingTrvRoleChange: (role: 'position' | 'open' | 'both') => void
  onSaveTrv: (trv: any) => void
  onCancelEditingTrv: () => void
  onDeleteTrv: (entityId: string) => void
}

export const AreaOverviewTab: React.FC<AreaOverviewTabProps> = ({
  area,
  temperature,
  enabled,
  editingTrvId,
  editingTrvName,
  editingTrvRole,
  onTemperatureChange,
  onTemperatureCommit,
  onTrvDialogOpen,
  onStartEditingTrv,
  onEditingTrvNameChange,
  onEditingTrvRoleChange,
  onSaveTrv,
  onCancelEditingTrv,
  onDeleteTrv,
}) => {
  const { t } = useTranslation()

  return (
    <Box sx={{ maxWidth: { xs: 800, lg: 1200 }, mx: 'auto', px: { xs: 0, sm: 0 } }}>
      <Paper sx={{ p: { xs: 2, sm: 3, md: 4 }, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
          <ThermostatIcon sx={{ fontSize: 32, color: 'primary.main' }} />
          <Typography
            variant="h5"
            color="text.primary"
            sx={{ fontSize: { xs: '1.1rem', sm: '1.25rem', md: '1.5rem' }, fontWeight: 600 }}
          >
            {t('areaDetail.temperatureControl')}
          </Typography>
        </Box>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ fontSize: { xs: '0.8rem', sm: '0.875rem' } }}
          >
            {t('areaDetail.targetTemperature')}
          </Typography>
          <Typography
            variant="h4"
            color="primary"
            data-testid="target-temperature-display"
            sx={{ fontSize: { xs: '1.75rem', sm: '2.125rem' } }}
          >
            {temperature}°C
          </Typography>
        </Box>
        <Slider
          value={temperature}
          sx={{
            '& .MuiSlider-thumb': {
              width: { xs: 24, sm: 20 },
              height: { xs: 24, sm: 20 },
            },
            '& .MuiSlider-track': {
              height: { xs: 6, sm: 4 },
            },
            '& .MuiSlider-rail': {
              height: { xs: 6, sm: 4 },
            },
          }}
          onChange={onTemperatureChange}
          onChangeCommitted={onTemperatureCommit}
          min={5}
          max={30}
          step={0.1}
          marks={[
            { value: 5, label: '5°' },
            { value: 15, label: '15°' },
            { value: 20, label: '20°' },
            { value: 25, label: '25°' },
            { value: 30, label: '30°' },
          ]}
          valueLabelDisplay="auto"
          disabled={!enabled || !!(area.preset_mode && area.preset_mode !== 'none')}
        />
        {enabled && area.state !== 'off' && area.preset_mode && area.preset_mode !== 'none' && (
          <Box mt={1} display="flex" alignItems="center" gap={1}>
            <BookmarkIcon fontSize="small" color="secondary" />
            <Typography
              variant="caption"
              color="text.secondary"
              dangerouslySetInnerHTML={{
                __html: t('areaDetail.presetModeActive', {
                  mode: t(`presets.${area.preset_mode}`).toUpperCase(),
                }),
              }}
            />
          </Box>
        )}

        {area.current_temperature !== undefined && (
          <>
            <Divider sx={{ my: 3 }} />
            <Box display="flex" justifyContent="space-between">
              <Typography variant="body1" color="text.secondary">
                {t('areaDetail.currentTemperature')}
              </Typography>
              <Typography variant="h5" color="text.primary">
                {area.current_temperature?.toFixed(1)}°C
              </Typography>
            </Box>

            {/* TRV status section */}
            <TrvList
              area={area}
              editingTrvId={editingTrvId}
              editingTrvName={editingTrvName}
              editingTrvRole={editingTrvRole}
              onTrvDialogOpen={onTrvDialogOpen}
              onStartEditingTrv={onStartEditingTrv}
              onEditingTrvNameChange={onEditingTrvNameChange}
              onEditingTrvRoleChange={onEditingTrvRoleChange}
              onSaveTrv={onSaveTrv}
              onCancelEditingTrv={onCancelEditingTrv}
              onDeleteTrv={onDeleteTrv}
            />
          </>
        )}
      </Paper>

      <Paper sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
          <SpeedIcon sx={{ fontSize: 32, color: 'primary.main' }} />
          <Typography variant="h5" color="text.primary" sx={{ fontWeight: 600 }}>
            {t('areaDetail.quickStats')}
          </Typography>
        </Box>
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' },
            gap: 3,
          }}
        >
          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {t('areaDetail.devices')}
            </Typography>
            <Typography variant="h6" color="text.primary">
              {t('areaDetail.devicesAssigned', { count: area.devices.length })}
            </Typography>
          </Box>
          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {t('areaDetail.status')}
            </Typography>
            <Typography variant="h6" color="text.primary" sx={{ textTransform: 'capitalize' }}>
              {area.state}
            </Typography>
          </Box>
          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {t('areaDetail.zoneId')}
            </Typography>
            <Typography variant="h6" color="text.primary" sx={{ fontSize: '1rem' }}>
              {area.id}
            </Typography>
          </Box>
        </Box>
      </Paper>
    </Box>
  )
}
