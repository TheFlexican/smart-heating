import React from 'react'
import {
  Box,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Button,
  Alert,
  TextField,
  Switch,
  FormControlLabel,
  Chip,
} from '@mui/material'
import ThermostatIcon from '@mui/icons-material/Thermostat'
import { useTranslation } from 'react-i18next'
import { Zone, Device } from '../../types'

export interface AvailableDevicesListProps {
  area: Zone
  availableDevices: Device[]
  showOnlyHeating: boolean
  deviceSearch: string
  onShowOnlyHeatingChange: (value: boolean) => void
  onDeviceSearchChange: (value: string) => void
  onAddDevice: (device: Device) => Promise<void>
}

export const AvailableDevicesList: React.FC<AvailableDevicesListProps> = ({
  area,
  availableDevices,
  showOnlyHeating,
  deviceSearch,
  onShowOnlyHeatingChange,
  onDeviceSearchChange,
  onAddDevice,
}) => {
  const { t } = useTranslation()

  const filterDevice = (device: Device) => {
    const typeMatch = !showOnlyHeating || ['climate', 'temperature'].includes(device.subtype || '')
    if (!deviceSearch) return typeMatch
    const searchLower = deviceSearch.toLowerCase()
    const nameMatch = (device.name || '').toLowerCase().includes(searchLower)
    const entityMatch = (device.entity_id || device.id || '').toLowerCase().includes(searchLower)
    const areaMatch = (device.ha_area_name || '').toLowerCase().includes(searchLower)
    return typeMatch && (nameMatch || entityMatch || areaMatch)
  }

  const filteredDevices = availableDevices.filter(filterDevice)

  const handleAddDevice = async (device: Device) => {
    try {
      await onAddDevice(device)
    } catch (error) {
      console.error('Failed to add device:', error)
    }
  }

  const getNoDevicesMessage = () => {
    if (deviceSearch) return t('areaDetail.noDevicesMatch', { search: deviceSearch })
    if (showOnlyHeating) return t('areaDetail.noClimateDevices')
    return t('areaDetail.noAdditionalDevices')
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 2,
        }}
      >
        <Typography variant="h6" color="text.primary">
          {t('areaDetail.availableDevices', { count: filteredDevices.length })}
        </Typography>
        <FormControlLabel
          control={
            <Switch
              checked={showOnlyHeating}
              onChange={e => onShowOnlyHeatingChange(e.target.checked)}
              color="primary"
            />
          }
          label={t('areaDetail.showOnlyClimate')}
        />
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        {t('areaDetail.availableDevicesDescription', { area: area.name })}
      </Typography>

      {/* Search Bar */}
      <TextField
        fullWidth
        size="small"
        placeholder={t('areaDetail.searchPlaceholder')}
        value={deviceSearch}
        onChange={e => onDeviceSearchChange(e.target.value)}
        sx={{ mb: 2 }}
      />

      {filteredDevices.length === 0 ? (
        <Alert severity="info">{getNoDevicesMessage()}</Alert>
      ) : (
        <List>
          {filteredDevices.map(device => (
            <ListItem
              data-testid={`available-device-${(device.entity_id || device.id).toLowerCase().replaceAll(' ', '-')}`}
              key={device.entity_id || device.id}
              sx={{
                border: 1,
                borderColor: 'divider',
                borderRadius: 1,
                mb: 1,
              }}
              secondaryAction={
                <Button
                  data-testid={`add-available-device-${(device.entity_id || device.id).toLowerCase().replaceAll(' ', '-')}`}
                  variant="contained"
                  size="small"
                  disabled={device.type === 'valve' && area?.heating_type === 'airco'}
                  title={
                    device.type === 'valve' && area?.heating_type === 'airco'
                      ? t('areaDetail.disabledForAirco', 'Disabled for Air Conditioner')
                      : undefined
                  }
                  onClick={() => handleAddDevice(device)}
                >
                  Add
                </Button>
              }
            >
              <ListItemIcon>
                <ThermostatIcon color="action" />
              </ListItemIcon>
              <ListItemText
                primary={
                  <Typography variant="body1" color="text.primary">
                    {device.name || device.entity_id || device.id}
                  </Typography>
                }
                secondary={
                  <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mt: 0.5 }}>
                    <Chip
                      label={String(device.type).replaceAll('_', ' ')}
                      size="small"
                      sx={{
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        background: (() => {
                          if (device.type === 'thermostat')
                            return 'linear-gradient(135deg, #ff6b35 0%, #f59e0b 100%)'
                          if (device.type === 'temperature_sensor')
                            return 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)'
                          if (device.type === 'valve')
                            return 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)'
                          return 'linear-gradient(135deg, #64748b 0%, #475569 100%)'
                        })(),
                        color: '#ffffff',
                        boxShadow: '0 2px 6px rgba(0, 0, 0, 0.15)',
                        border: 'none',
                      }}
                    />
                    {device.subtype && (
                      <Chip
                        label={device.subtype}
                        size="small"
                        sx={{
                          fontSize: '0.7rem',
                          fontWeight: 600,
                          background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                          color: '#ffffff',
                          boxShadow: '0 2px 6px rgba(16, 185, 129, 0.3)',
                          border: 'none',
                        }}
                      />
                    )}
                    <Typography variant="caption" color="text.secondary" component="span">
                      {device.entity_id || device.id}
                    </Typography>
                  </Box>
                }
                slotProps={{ secondary: { component: 'div' } }}
              />
            </ListItem>
          ))}
        </List>
      )}
    </Paper>
  )
}
