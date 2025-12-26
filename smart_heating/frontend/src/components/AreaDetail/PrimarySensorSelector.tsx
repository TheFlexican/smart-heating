import React from 'react'
import { Box, Paper, Typography, FormControl, InputLabel, Select, MenuItem } from '@mui/material'
import ThermostatIcon from '@mui/icons-material/Thermostat'
import { useTranslation } from 'react-i18next'
import { Zone } from '../../types'

export interface PrimarySensorSelectorProps {
  area: Zone
  onPrimarySensorChange: (sensorId: string | null) => Promise<void>
}

export const PrimarySensorSelector: React.FC<PrimarySensorSelectorProps> = ({
  area,
  onPrimarySensorChange,
}) => {
  const { t } = useTranslation()

  const handleChange = async (value: string) => {
    try {
      const sensorId = value === 'auto' ? null : value
      await onPrimarySensorChange(sensorId)
    } catch (error) {
      console.error('Failed to set primary temperature sensor:', error)
      alert('Failed to set primary temperature sensor. Check console for details.')
    }
  }

  return (
    <Paper sx={{ p: { xs: 2, sm: 3, md: 4 }, mb: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
        <ThermostatIcon sx={{ fontSize: 32, color: 'primary.main' }} />
        <Typography variant="h5" color="text.primary" sx={{ fontWeight: 600 }}>
          {t('areaDetail.primaryTemperatureSensor')}
        </Typography>
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('areaDetail.primaryTemperatureSensorDescription')}
      </Typography>
      <FormControl fullWidth>
        <InputLabel>{t('areaDetail.temperatureSensor')}</InputLabel>
        <Select
          value={area.primary_temperature_sensor || 'auto'}
          label={t('areaDetail.temperatureSensor')}
          onChange={e => handleChange(e.target.value)}
        >
          <MenuItem value="auto">
            <em>{t('areaDetail.autoAllSensors')}</em>
          </MenuItem>
          {area.devices
            .filter(d => d.type === 'temperature_sensor' || d.type === 'thermostat')
            .map(device => {
              const deviceId = device.entity_id || device.id
              return (
                <MenuItem key={deviceId} value={deviceId}>
                  {device.name || deviceId} (
                  {device.type === 'thermostat'
                    ? t('areaDetail.thermostat')
                    : t('areaDetail.tempSensor')}
                  )
                </MenuItem>
              )
            })}
        </Select>
      </FormControl>
    </Paper>
  )
}
